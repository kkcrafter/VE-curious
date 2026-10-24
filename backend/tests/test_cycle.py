import pytest
from fastapi.testclient import TestClient

from app import core, db
from app.main import app

D1 = {"X-Driver-Id": "d1"}
D2 = {"X-Driver-Id": "d2"}
LOCK = "lock-0002"  # bay-1


@pytest.fixture
def c():
    with TestClient(app) as client:
        db.reset()
        core.adapter.reset()
        core.tick()  # no background poll in tests; unknown last_seen would show "unverified"
        yield client


def reserve(c, headers=D1, bay="bay-1"):
    return c.post("/api/reservations", json={"bayId": bay}, headers=headers)


def get(c, r, headers=D1):
    return c.get(f"/api/reservations/{r['id']}", headers=headers)


def plate(p):
    core.on_hardware_event({"kind": "plate", "lock_id": LOCK, "plate": p})


def presence(occupied):
    core.on_hardware_event({"kind": "presence", "lock_id": LOCK, "occupied": occupied})


def test_s1_full_cycle_on_mock(c):
    r = reserve(c).json()
    assert r["state"] == "RESERVED" and r["allowedActions"] == ["cancel"] and r["plate"] == "M-AB 1234"
    assert c.get("/api/bays/bay-1").json()["status"] == "reserved"
    assert core.adapter.locks[LOCK]["arm"] == "raised"

    plate("X-YZ 999")  # stranger: no check-in (PLATE_MISMATCH comes with #22)
    assert get(c, r).json()["state"] == "RESERVED"

    plate("mab1234")  # normalised match
    assert get(c, r).json()["state"] == "ARRIVED" and core.adapter.locks[LOCK]["arm"] == "lowered"

    presence(True)
    assert c.post(f"/api/reservations/{r['id']}/charging", json={"action": "start"}, headers=D1).json()["state"] == "CHARGING"
    presence(False)
    assert get(c, r).json()["state"] == "COMPLETED"
    assert c.get("/api/bays/bay-1").json()["status"] == "free"

    log = db.rows("SELECT kind, payload FROM event_log")
    assert not any("X-YZ" in row["payload"] for row in log)  # stranger's plate is masked
    assert sum(row["kind"] == "adapter_call" for row in log) == 3  # reserve, unlock, release


def test_conflicts_and_idempotency(c):
    first = c.post("/api/reservations", json={"bayId": "bay-1"}, headers={**D1, "Idempotency-Key": "k1"}).json()
    again = c.post("/api/reservations", json={"bayId": "bay-1"}, headers={**D1, "Idempotency-Key": "k1"}).json()
    assert again["id"] == first["id"]
    assert reserve(c, headers=D2).json()["error"]["code"] == "bay_taken"
    assert reserve(c, bay="bay-2").json()["error"]["code"] == "driver_has_active"
    assert reserve(c, headers=D2, bay="bay-2").status_code == 201


def test_cancel_and_invalid_action(c):
    r = reserve(c).json()
    assert c.post(f"/api/reservations/{r['id']}/charging", json={"action": "start"}, headers=D1).status_code == 409
    assert c.post(f"/api/reservations/{r['id']}/cancel", headers=D1).json()["state"] == "CANCELLED"
    assert get(c, r, headers=D2).status_code == 404  # not d2's reservation
    assert reserve(c, headers=D2).status_code == 201  # bay free again


def test_hardware_failure_gives_failed(c):
    core.adapter.fail_next.add("reserve")
    resp = reserve(c)
    assert resp.status_code == 502 and resp.json()["error"]["code"] == "hardware_error"
    assert c.get("/api/me/reservations", headers=D1).json()[0]["state"] == "FAILED"
    assert reserve(c).status_code == 201  # nothing stuck


def test_auth_and_bad_input(c):
    assert reserve(c, headers={}).json()["error"]["code"] == "unauthorized"
    assert c.post("/api/reservations", json={}, headers=D1).status_code == 400


def test_stale_camera_is_never_free(c):
    core.adapter.locks[LOCK].update(online=False, lastSeen="2020-01-01T00:00:00Z")
    db.update("bays", "bay-1", last_seen_at="2020-01-01T00:00:00Z")
    core.tick()
    assert c.get("/api/bays/bay-1").json()["status"] == "unverified"
