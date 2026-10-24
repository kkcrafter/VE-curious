"""HTTP API. Contract: docs/design/backend-outline.md §3."""

import hmac
import json
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, core, db, hardware_events, machine
from .core import ApiError


@asynccontextmanager
async def lifespan(app):
    db.init()
    if config.POLL_SECONDS:
        threading.Thread(target=core.run_ticker, daemon=True).start()
    if config.ADAPTER == "ecurious":
        threading.Thread(target=hardware_events.run, daemon=True).start()
    yield


app = FastAPI(title="VE-curious backend", lifespan=lifespan)
api = APIRouter(prefix="/api")
dev = APIRouter(prefix="/api/dev")


@app.exception_handler(ApiError)
def api_error(request: Request, e: ApiError):
    return JSONResponse({"error": {"code": e.code, "message": e.message}}, status_code=e.status)


@app.exception_handler(RequestValidationError)
def bad_request(request: Request, e: RequestValidationError):
    return JSONResponse({"error": {"code": "bad_request", "message": str(e.errors())}}, status_code=400)


# ---- serialisation ----

def reservation_json(r):
    return {
        "id": r["id"],
        "bayId": r["bay_id"],
        "plate": r["plate"],
        "state": r["state"],
        "blockedReason": r["blocked_reason"],
        "faultReason": r["fault_reason"],
        "slotStart": r["slot_start"],
        "feeCents": r["fee_cents"],
        "graceDeadline": r["grace_deadline"],
        "serverTime": db.iso(db.now()),
        "allowedActions": machine.allowed_actions(r["state"]),
        "charging": core.charging(r),  # simulated [GAP C3]; null before CHARGING
        "createdAt": r["created_at"],
        "updatedAt": r["updated_at"],
    }


def bay_json(b):
    last_seen = db.parse(b["last_seen_at"])
    if b["out_of_service"]:
        status = "out_of_service"
    elif not last_seen or db.now() - last_seen > timedelta(seconds=config.CAMERA_STALE_SECONDS):
        status = "unverified"  # unknown camera health is never "free"
    elif db.held_reservation(b["id"]):
        status = "reserved"
    elif b["occupied"]:
        status = "occupied"
    else:
        status = "free"
    return {"id": b["id"], "geId": b["ge_id"], "name": b["name"], "status": status, "lastSeenAt": b["last_seen_at"]}


# ---- auth: email + password, opaque session token (prototype) ----
# ponytail: sessions never expire and logins are not rate-limited; add both before any public deploy

def current_driver(authorization: str | None = Header(None)):
    token = (authorization or "").removeprefix("Bearer ")
    s = db.one("SELECT driver_id FROM sessions WHERE token = ?", token)
    if not s:
        raise ApiError(401, "unauthorized", "Missing or unknown session token")
    return s["driver_id"]


def own_reservation(reservation_id: str, driver: str = Depends(current_driver)):
    r = db.one("SELECT * FROM reservations WHERE id = ? AND driver_id = ?", reservation_id, driver)
    if not r:
        raise ApiError(404, "not_found", f"Reservation {reservation_id} not found")
    return r


def get_bay(bay_id):
    b = db.one("SELECT * FROM bays WHERE id = ?", bay_id)
    if not b:
        raise ApiError(404, "not_found", f"Bay {bay_id} not found")
    return b


# ---- driver routes ----

class LoginIn(BaseModel):
    email: str
    password: str


def driver_json(d):
    return {"id": d["id"], "name": d["name"], "plate": d["plate"], "email": d["email"]}


@api.post("/login")
def login(body: LoginIn):
    d = db.one("SELECT * FROM drivers WHERE email = ?", body.email.strip().lower())
    if not d or not db.check_password(body.password, d["password_hash"]):
        raise ApiError(401, "bad_credentials", "Wrong email or password")
    token = secrets.token_urlsafe(32)
    db.execute("INSERT INTO sessions VALUES (?, ?, ?)", token, d["id"], db.iso(db.now()))
    return {"token": token, "driver": driver_json(d)}


@api.post("/logout", status_code=204)
def logout(authorization: str | None = Header(None)):
    db.execute("DELETE FROM sessions WHERE token = ?", (authorization or "").removeprefix("Bearer "))


@api.get("/me")
def me(driver: str = Depends(current_driver)):
    return driver_json(db.one("SELECT * FROM drivers WHERE id = ?", driver))


class ReservationIn(BaseModel):
    bayId: str
    plate: str | None = None  # defaults to the driver's profile plate
    slotStart: str | None = None  # a "start" from GET /bays/{id}/slots; None = now


class ChargingIn(BaseModel):
    action: Literal["start", "stop"]


@api.get("/bays")
def list_bays():
    return [bay_json(b) for b in db.rows("SELECT * FROM bays ORDER BY id")]


@api.get("/bays/{bay_id}")
def read_bay(bay_id: str):
    return bay_json(get_bay(bay_id))


@api.get("/bays/{bay_id}/slots")
def bay_slots(bay_id: str):
    get_bay(bay_id)
    return core.slots(bay_id)


@api.post("/reservations", status_code=201)
def create_reservation(
    body: ReservationIn, driver: str = Depends(current_driver), idempotency_key: str | None = Header(None)
):
    plate = body.plate or db.one("SELECT plate FROM drivers WHERE id = ?", driver)["plate"]
    return reservation_json(core.create_reservation(driver, body.bayId, plate, idempotency_key, body.slotStart))


@api.get("/reservations/{reservation_id}")
def read_reservation(r=Depends(own_reservation)):
    return reservation_json(r)


@api.get("/me/reservations")
def my_reservations(active: bool = False, driver: str = Depends(current_driver)):
    rs = db.rows("SELECT * FROM reservations WHERE driver_id = ? ORDER BY created_at DESC", driver)
    return [reservation_json(r) for r in rs if not active or r["state"] not in machine.TERMINAL]


@api.post("/reservations/{reservation_id}/cancel")
def cancel(r=Depends(own_reservation)):
    return reservation_json(core.apply(r["id"], "cancel"))


@api.post("/reservations/{reservation_id}/charging")
def charging(body: ChargingIn, r=Depends(own_reservation)):
    # [GAP C3] stand-in until Ecurious says how charging is started / observed (#20)
    return reservation_json(core.apply(r["id"], f"{body.action}_charging"))


@api.get("/config")
def client_config():
    # ponytail: key is visible to any browser that loads the page; GoingElectric terms want the device
    # to fetch directly, so we never proxy or cache their data. Visible-key question: [GAP C8 Q3]
    return {"goingelectricKey": config.GOINGELECTRIC_API_KEY}


# ---- operator (rest of #26 later) ----

def require_operator(x_operator_token: str | None = Header(None)):
    if config.OPERATOR_TOKEN and not hmac.compare_digest(x_operator_token or "", config.OPERATOR_TOKEN):
        raise ApiError(401, "unauthorized", "Missing or wrong X-Operator-Token")


@api.get("/operator/events", dependencies=[Depends(require_operator)])
def operator_events(limit: int = Query(100, ge=1, le=500)):
    rs = db.rows("SELECT * FROM event_log ORDER BY id DESC LIMIT ?", limit)
    return [
        {"ts": r["ts"], "reservationId": r["reservation_id"], "bayId": r["bay_id"], "kind": r["kind"], "payload": json.loads(r["payload"])}
        for r in rs
    ]


FRONTEND = Path(__file__).parents[2] / "frontend"


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/test", include_in_schema=False)
def hardware_test_page():
    # ponytail: one static page to watch the shared lock live; the real operator view is frontend #36
    return FileResponse(Path(__file__).with_name("test.html"))


# ---- dev controls (mock adapter only) ----

class PlateIn(BaseModel):
    bayId: str
    plate: str


class PresenceIn(BaseModel):
    bayId: str
    occupied: bool


class CameraIn(BaseModel):
    bayId: str
    online: bool


class FailIn(BaseModel):
    call: Literal["reserve", "release", "unlock"]


def mock_lock(bay_id):
    return core.adapter.locks[get_bay(bay_id)["lock_id"]]


@dev.post("/plate")
def dev_plate(body: PlateIn):
    lock_id = get_bay(body.bayId)["lock_id"]
    if core.adapter.locks[lock_id]["online"]:  # a blind camera sees nothing
        core.on_hardware_event({"kind": "plate", "lock_id": lock_id, "plate": body.plate})
    return {"ok": True}


@dev.post("/presence")
def dev_presence(body: PresenceIn):
    lock = mock_lock(body.bayId)
    lock["occupied"] = body.occupied
    if lock["online"]:
        core.on_hardware_event({"kind": "presence", "lock_id": get_bay(body.bayId)["lock_id"], "occupied": body.occupied})
    return {"ok": True}


@dev.post("/camera")
def dev_camera(body: CameraIn):
    mock_lock(body.bayId)["online"] = body.online
    return {"ok": True}


@dev.post("/fail-next")
def dev_fail_next(body: FailIn):
    core.adapter.fail_next.add(body.call)
    return {"ok": True}


@dev.post("/reset")
def dev_reset():
    db.reset()
    core.adapter.reset()
    return {"ok": True}


app.include_router(api)
if config.ADAPTER == "mock":
    app.include_router(dev)
