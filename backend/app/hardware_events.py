"""Ecurious SSE stream -> core.on_hardware_event. Reconnects with backoff; core.tick polls while it is down."""

import json
import time

import httpx

from . import config, core, db


def parse(name, data):
    """Live stream sends 'lock:'-prefixed names (lock:car_presence); the docs show bare ones. Accept both."""
    name, lock_id = name.removeprefix("lock:"), data.get("lockId")
    if name == "photo_captured":
        return {"kind": "plate", "lock_id": lock_id, "plate": data.get("licensePlate")}
    if name in ("car_presence", "vehicle_presence"):
        presence = data.get("presence") or data.get("carPresence") or data.get("state")
        return {"kind": "presence", "lock_id": lock_id, "occupied": presence == "occupied"}
    if name in ("status_change", "status_changed"):
        return {"kind": "arm", "lock_id": lock_id, "status": data.get("status")}
    if name == "alarm":
        return {"kind": "alarm", "lock_id": lock_id, "error": data.get("error")}
    if name == "heartbeat":
        return {"kind": "heartbeat", "lock_id": lock_id}
    return None  # "connected" and unknown events


def run():
    backoff = 1
    while True:
        try:
            with httpx.stream(
                "GET", f"{config.ECURIOUS_BASE_URL}/api/v1/events",
                headers={"X-API-Key": config.ECURIOUS_API_KEY}, timeout=httpx.Timeout(10, read=90),
            ) as r:
                r.raise_for_status()
                core.stream_connected.set()
                db.log("sse_connected")
                backoff, name = 1, None
                for line in r.iter_lines():
                    if line.startswith("event:"):
                        name = line[6:].strip()
                    elif line.startswith("data:") and name:
                        ev = parse(name, json.loads(line[5:]))
                        if ev and ev["lock_id"] in config.LOCK_IDS:
                            core.on_hardware_event(ev)
                    elif not line:
                        name = None
            error = "stream closed"
        except Exception as e:  # any failure: reconnect, polling covers the gap
            error = repr(e)
        core.stream_connected.clear()
        db.log("sse_disconnected", error=error, retry_in=backoff)
        time.sleep(backoff)
        backoff = min(backoff * 2, 30)
