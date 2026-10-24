"""Reservation core: the only place that changes reservation state and calls hardware."""

import secrets
import sqlite3
import threading
import time
from datetime import timedelta
from zoneinfo import ZoneInfo

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
        if (effect := machine.EFFECTS.get(nxt)) and r["state"] != "SCHEDULED":  # SCHEDULED never touched hardware
            # ponytail: a failed release/unlock keeps our state and shows in the event log; reconciliation loop if it bites
            hardware(effect, r["bay_id"], reservation_id)
        return db.one("SELECT * FROM reservations WHERE id = ?", reservation_id)


def charging(r):
    """Simulated charger session [GAP C3]: None until CHARGING, frozen once COMPLETED.
    Start/end times come from the event log; energy from constant power, sped up for the demo."""
    def entered(state):
        row = db.one(
            "SELECT ts FROM event_log WHERE reservation_id = ? AND kind = 'state_change' AND json_extract(payload, '$.to') = ?",
            r["id"], state,
        )
        return row and row["ts"]

    start, end = entered("CHARGING"), entered("COMPLETED")
    if not start:
        return None
    # ponytail: constant power until full; a taper curve or real charger meter values (OCPP) replace this
    seconds = ((db.parse(end) if end else db.now()) - db.parse(start)).total_seconds() * config.CHARGE_SPEEDUP
    room = config.BATTERY_KWH * (100 - config.START_SOC) / 100
    kwh = min(config.CHARGE_KW * seconds / 3600, room)
    return {
        "startedAt": start,
        "endedAt": end,
        "durationSeconds": round(seconds),
        "energyKwh": round(kwh, 2),
        "powerKw": 0 if end or kwh >= room else config.CHARGE_KW,
        "socPercent": round(config.START_SOC + kwh / config.BATTERY_KWH * 100),
        "pricePerKwhCents": config.KWH_CENTS,
        "costCents": round(kwh * config.KWH_CENTS),
        "simulated": True,
    }


def fee_cents(start):
    hour = start.astimezone(ZoneInfo(config.TIMEZONE)).hour
    peak = config.PEAK_HOURS[0] <= hour < config.PEAK_HOURS[1]
    return round(config.FEE_CENTS * (config.PEAK_FACTOR if peak else 1))


def slots(bay_id):
    """Slots a driver can book: "now" (start None) plus the next SLOT_COUNT slots, each with its fee.
    end = latest arrival: the bay is held from start until end. Later slots: the whole slot. Now: at least
    GRACE_MINUTES, rounded up to the next slot boundary so every end time reads :00 or :30."""
    t = db.now().replace(second=0, microsecond=0)
    first = t + timedelta(minutes=config.SLOT_MINUTES - t.minute % config.SLOT_MINUTES)
    starts = [None] + [first + timedelta(minutes=config.SLOT_MINUTES * i) for i in range(config.SLOT_COUNT)]
    now_end = first
    while now_end < db.now() + timedelta(minutes=config.GRACE_MINUTES):
        now_end += timedelta(minutes=config.SLOT_MINUTES)
    # Booked windows [start, end): slot start (or booking time for "now") until latest arrival.
    # ponytail: overlap check in Python under db.lock (one process); Postgres EXCLUDE on tstzrange if we ever scale out
    booked = [(r["slot_start"] or r["created_at"], r["grace_deadline"] or "9999") for r in db.active_reservations(bay_id)]
    held = db.held_reservation(bay_id)  # bay in use now: "now" is never free, whatever its window says
    out = []
    for s in starts:
        start = db.iso(s or db.now())
        end = db.iso(s + timedelta(minutes=config.SLOT_MINUTES) if s else now_end)
        free = not any(a < end and start < b for a, b in booked) and not (s is None and held)
        out.append({"start": s and start, "end": end, "feeCents": fee_cents(s or db.now()), "available": free})
    return out


def hold(rid, bay_id, end):
    """Ask the hardware to hold the bay until end (latest arrival). Returns the new row, or None on failure."""
    if hardware("reserve", bay_id, rid):
        return apply(rid, "reserve_ok", grace_deadline=end)
    apply(rid, "reserve_failed")
    return None


def create_reservation(driver_id, bay_id, plate, idempotency_key=None, slot_start=None):
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
        slot = next((s for s in slots(bay_id) if s["start"] == slot_start), None)  # price comes from us, never the client
        if not slot:
            raise ApiError(400, "bad_slot", "Slot not offered (any more); reload the slots")
        if not slot["available"]:
            raise ApiError(409, "slot_taken", "Someone already booked this slot; pick another")
        state = "SCHEDULED" if slot_start else "REQUESTED"
        rid, ts = "r_" + secrets.token_hex(4), db.iso(db.now())
        try:
            db.execute(
                "INSERT INTO reservations (id, bay_id, driver_id, plate, state, slot_start, grace_deadline, fee_cents, idempotency_key, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rid, bay_id, driver_id, plate, state, slot_start, slot_start and slot["end"], slot["feeCents"], idempotency_key, ts, ts,
            )
        except sqlite3.IntegrityError as e:  # partial unique indexes: one active reservation per bay / per driver
            if "bay_id" in str(e):
                raise ApiError(409, "bay_taken", "Bay already reserved")
            raise ApiError(409, "driver_has_active", "You already have an active reservation")
        db.log("state_change", rid, bay_id, frm=None, to=state, event="request")
        if slot_start:  # soft hold: bay stays open to walk-ins until the slot starts (idea #4)
            return db.one("SELECT * FROM reservations WHERE id = ?", rid)
        if r := hold(rid, bay_id, slot["end"]):
            return r
        raise ApiError(502, "hardware_error", "Could not reserve the bay; try again or pick another bay")


def start_due_slots():
    """SCHEDULED -> RESERVED once the slot starts. A failed hold ends in FAILED; the driver sees it on the next poll."""
    # ponytail: a walk-in or a driver still charging at slot start only delays the hold here; telling the next
    # driver is the BLOCKED flow (#22-#24). An expired RESERVED also waits until the no-show sweep ends it.
    with db.lock:
        for r in db.rows("SELECT * FROM reservations WHERE state = 'SCHEDULED' AND slot_start <= ?", db.iso(db.now())):
            if not db.held_reservation(r["bay_id"]):
                hold(r["id"], r["bay_id"], r["grace_deadline"])


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

        r = db.held_reservation(bay["id"])
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
    start_due_slots()
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
