"""Hardware adapters. Same methods on both; core picks one by ADAPTER.

reserve(lock_id)   raise the arm, hardware whitelist empty
release(lock_id)   lower the arm and keep it down (bay open again)
unlock(lock_id)    lower the arm for the booked car (check-in)
status(lock_id)    {occupied, lastSeen, raw}
latest_plate(lock_id) -> (plate, timestamp) | None
"""

import httpx

from . import config, db


class HardwareError(Exception):
    pass


class MockAdapter:
    """In-memory locks for development and demo fallback. Dev routes drive it."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.locks = {
            lock_id: {"arm": "lowered", "occupied": False, "online": True, "lastSeen": db.iso(db.now())}
            for lock_id in config.LOCK_IDS
        }
        self.fail_next = set()

    def _check(self, call, lock_id):
        if call in self.fail_next:
            self.fail_next.discard(call)
            raise HardwareError(f"mock {call} failed (dev fail-next)")
        if not self.locks[lock_id]["online"]:
            raise HardwareError("lock offline")

    def reserve(self, lock_id):
        self._check("reserve", lock_id)
        self.locks[lock_id]["arm"] = "raised"

    def release(self, lock_id):
        self._check("release", lock_id)
        self.locks[lock_id]["arm"] = "lowered"

    def unlock(self, lock_id):
        self._check("unlock", lock_id)
        self.locks[lock_id]["arm"] = "lowered"

    def status(self, lock_id):
        lock = self.locks[lock_id]
        if lock["online"]:
            lock["lastSeen"] = db.iso(db.now())
        return {"occupied": lock["occupied"], "lastSeen": lock["lastSeen"], "raw": dict(lock)}

    def latest_plate(self, lock_id):
        return None  # mock plates arrive through POST /api/dev/plate


class EcuriousAdapter:
    """Ecurious parking-lock service. API notes: docs/design/state-machine.md."""

    def __init__(self):
        self.http = httpx.Client(
            base_url=config.ECURIOUS_BASE_URL, headers={"X-API-Key": config.ECURIOUS_API_KEY}, timeout=10
        )

    def _request(self, method, path, body=None):
        try:
            r = self.http.request(method, path, json=body)
        except httpx.TimeoutException:
            raise HardwareError("timeout")
        except httpx.HTTPError as e:
            raise HardwareError(f"network: {e}")
        if r.status_code == 403:
            raise HardwareError("forbidden: lock not assigned to our API key")
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.is_error or data.get("success") is False:
            raise HardwareError(f"{r.status_code}: {data.get('error') or data.get('message') or r.text[:200]}")
        return data

    def reserve(self, lock_id):
        # Empty whitelist: the arm only lowers after our own plate check, so PLATE_MISMATCH and the log see it first
        self._request("POST", f"/api/v1/locks/{lock_id}/whitelist", {"plates": []})
        self._request("POST", f"/api/v1/locks/{lock_id}/lock", {"cancelAutoLift": True})

    def release(self, lock_id):
        self._request("POST", f"/api/v1/locks/{lock_id}/unlock", {"cancelAutoLift": True})

    def unlock(self, lock_id):
        # Default auto-lift: the arm re-raises if the car does not drive in (timeout length unknown)
        self._request("POST", f"/api/v1/locks/{lock_id}/unlock", {})

    def status(self, lock_id):
        lock = self._request("GET", f"/api/v1/locks/{lock_id}")["lock"]
        return {"occupied": lock["carPresence"] == "occupied", "lastSeen": lock["lastSeenAt"], "raw": lock}

    def latest_plate(self, lock_id):
        try:
            d = self._request("GET", f"/api/v1/locks/{lock_id}/plate/latest")
        except HardwareError:
            return None  # also "no plate recognised yet"
        return d.get("licensePlate"), d.get("timestamp")
