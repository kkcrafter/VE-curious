"""Hardware adapters. Same methods on both; core picks one by ADAPTER.

reserve(lock_id)   raise the arm, hardware whitelist empty
release(lock_id)   lower the arm and keep it down (bay open again)
unlock(lock_id)    lower the arm for the booked car (check-in)
status(lock_id)    {occupied, lastSeen, raw}
"""

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
