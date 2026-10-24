"""HTTP API. Contract: docs/design/backend-outline.md §3."""

from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from . import config, db
from .core import ApiError


@asynccontextmanager
async def lifespan(app):
    db.init()
    yield


app = FastAPI(title="Ve-curious backend", lifespan=lifespan)
api = APIRouter(prefix="/api")


@app.exception_handler(ApiError)
def api_error(request: Request, e: ApiError):
    return JSONResponse({"error": {"code": e.code, "message": e.message}}, status_code=e.status)


@app.exception_handler(RequestValidationError)
def bad_request(request: Request, e: RequestValidationError):
    return JSONResponse({"error": {"code": "bad_request", "message": str(e.errors())}}, status_code=400)


# ---- serialisation ----

def bay_json(b):
    last_seen = db.parse(b["last_seen_at"])
    if b["out_of_service"]:
        status = "out_of_service"
    elif not last_seen or db.now() - last_seen > timedelta(seconds=config.CAMERA_STALE_SECONDS):
        status = "unverified"  # unknown camera health is never "free"
    elif db.active_reservation("bay_id", b["id"]):
        status = "reserved"
    elif b["occupied"]:
        status = "occupied"
    else:
        status = "free"
    return {"id": b["id"], "geId": b["ge_id"], "name": b["name"], "status": status, "lastSeenAt": b["last_seen_at"]}


def get_bay(bay_id):
    b = db.one("SELECT * FROM bays WHERE id = ?", bay_id)
    if not b:
        raise ApiError(404, "not_found", f"Bay {bay_id} not found")
    return b


# ---- routes ----

@api.get("/bays")
def list_bays():
    return [bay_json(b) for b in db.rows("SELECT * FROM bays ORDER BY id")]


@api.get("/bays/{bay_id}")
def read_bay(bay_id: str):
    return bay_json(get_bay(bay_id))


app.include_router(api)
