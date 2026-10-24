"""Reservation core: the only place that changes reservation state and calls hardware."""

import secrets
import sqlite3
import threading
import time
from datetime import timedelta

from . import config, db, machine
from .adapters import EcuriousAdapter, HardwareError, MockAdapter

adapter = EcuriousAdapter() if config.ADAPTER == "ecurious" else MockAdapter()
stream_connected = threading.Event()  # set by hardware_events while the SSE stream is up
_last_plate = {}  # lock_id -> timestamp of the latest plate seen by polling


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def norm_plate(plate):
    return "".join(ch for ch in (plate or "").upper() if ch.isalnum())


def mask_plate(plate):
    # GDPR: plates of non-customers pass through events; log only a prefix [TEAM B6]
    return plate[:2] + "***" if plate else None


def hardware(call, bay_id, reservation_id=None):
    """Run one adapter call and log it. Returns True on success; errors are logged, not raised."""
    lock_id = db.one("SELECT lock_id FROM bays WHERE id = ?", bay_id)["lock_id"]
    try:
        getattr(adapter, call)(lock_id)
    except HardwareError as e:
        db.log("adapter_call", reservation_id, bay_id, call=call, ok=False, error=str(e))
        return False
    db.log("adapter_call", reservation_id, bay_id, call=call, ok=True)
    return True


def apply(reservation_id, event, **fields):
    with db.lock:
        r = db.one("SELECT * FROM reservations WHERE id = ?", reservation_id)
        nxt = machine.next_state(r["state"], event)
        if not nxt:
            raise ApiError(409, "invalid_action", f"'{event}' is not allowed in state {r['state']}")
        db.update("reservations", reservation_id, state=nxt, **fields)
        db.log("state_change", reservation_id, r["bay_id"], frm=r["state"], to=nxt, event=event)
        if effect := machine.EFFECTS.get(nxt):
            # ponytail: a failed release/unlock keeps our state and shows in the event log; reconciliation loop if it bites
            hardware(effect, r["bay_id"], reservation_id)
        return db.one("SELECT * FROM reservations WHERE id = ?", reservation_id)


def create_reservation(driver_id, bay_id, plate, idempotency_key=None):
    with db.lock:
        if idempotency_key and (r := db.one(
            "SELECT * FROM reservations WHERE driver_id = ? AND idempotency_key = ?", driver_id, idempotency_key
        )):
            return r
        bay = db.one("SELECT * FROM bays WHERE id = ?", bay_id)
        if not bay:
            raise ApiError(404, "not_found", f"Bay {bay_id} not found")
        if bay["out_of_service"]:
            raise ApiError(409, "out_of_service", "Bay is out of service")
        rid, ts = "r_" + secrets.token_hex(4), db.iso(db.now())
        try:
            db.execute(
                "INSERT INTO reservations (id, bay_id, driver_id, plate, state, idempotency_key, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, 'REQUESTED', ?, ?, ?)",
                rid, bay_id, driver_id, plate, idempotency_key, ts, ts,
            )
        except sqlite3.IntegrityError as e:  # partial unique indexes: one active reservation per bay / per driver
            if "bay_id" in str(e):
                raise ApiError(409, "bay_taken", "Bay already reserved")
            raise ApiError(409, "driver_has_active", "You already have an active reservation")
        db.log("state_change", rid, bay_id, frm=None, to="REQUESTED", event="request")
        if hardware("reserve", bay_id, rid):
            grace = db.iso(db.now() + timedelta(minutes=config.GRACE_MINUTES))
            return apply(rid, "reserve_ok", grace_deadline=grace)
        apply(rid, "reserve_failed")
        raise ApiError(502, "hardware_error", "Could not reserve the bay; try again or pick another bay")


def on_hardware_event(ev):
    """ev: {kind: plate|presence|arm|alarm|heartbeat, lock_id, ...} from SSE, polling or dev routes."""
    with db.lock:
        bay = db.one("SELECT * FROM bays WHERE lock_id = ?", ev["lock_id"])
        if not bay:
            return
        fields = {"last_seen_at": db.iso(db.now())}
        if ev["kind"] == "presence":
            fields["occupied"] = int(ev["occupied"])
        db.update("bays", bay["id"], **fields)
        if ev["kind"] == "heartbeat":
            return
        payload = {**ev, "event": ev["kind"], "plate": mask_plate(ev.get("plate"))}
        del payload["kind"]
        db.log("hardware_event", None, bay["id"], **payload)

        r = db.active_reservation("bay_id", bay["id"])
        if not r:
            return
        if ev["kind"] == "plate":
            match = norm_plate(ev["plate"]) == norm_plate(r["plate"])
            db.log("plate_check", r["id"], bay["id"], match=match)
            if match and machine.next_state(r["state"], "plate_match"):
                apply(r["id"], "plate_match")
            # plate mismatch -> PLATE_MISMATCH comes with #22
        elif ev["kind"] == "presence" and not ev["occupied"] and machine.next_state(r["state"], "vehicle_left"):
            apply(r["id"], "vehicle_left")


def tick():
    """Poll every bay: refresh last seen and presence, and catch plates/presence missed while SSE was down."""
    for bay in db.rows("SELECT * FROM bays"):
        try:
            s = adapter.status(bay["lock_id"])
        except HardwareError:
            continue  # last_seen_at goes stale and the bay shows "unverified"
        seen = max(filter(None, [db.parse(bay["last_seen_at"]), db.parse(s["lastSeen"])]))
        db.update("bays", bay["id"], last_seen_at=db.iso(seen))
        if s["occupied"] != bool(bay["occupied"]):
            on_hardware_event({"kind": "presence", "lock_id": bay["lock_id"], "occupied": s["occupied"]})
        if not stream_connected.is_set() and (latest := adapter.latest_plate(bay["lock_id"])):
            plate, ts = latest
            known = _last_plate.get(bay["lock_id"])
            _last_plate[bay["lock_id"]] = ts
            if known and ts != known:  # first poll is only a baseline, not an arrival
                on_hardware_event({"kind": "plate", "lock_id": bay["lock_id"], "plate": plate})


def run_ticker():
    while True:
        try:
            tick()
        except Exception as e:  # keep polling whatever one round throws
            db.log("tick_error", error=repr(e))
        time.sleep(config.POLL_SECONDS)
