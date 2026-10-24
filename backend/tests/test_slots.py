from datetime import datetime, timedelta

from app import config, core, db
from test_cycle import D1, D2, LOCK, c, get  # noqa: F401  (c is the fixture)


def test_slots_list_now_first_with_fee(c):
    s = c.get("/api/bays/bay-1/slots").json()
    assert s[0]["start"] is None and len(s) == config.SLOT_COUNT + 1
    assert all(x["available"] and x["feeCents"] in (200, 300) for x in s)
    assert all(db.parse(x["end"]) - db.parse(x["start"]) == timedelta(minutes=config.SLOT_MINUTES) for x in s[1:])
    now_end = db.parse(s[0]["end"])
    assert now_end.minute % config.SLOT_MINUTES == 0 and now_end - db.now() >= timedelta(minutes=config.GRACE_MINUTES)


def test_peak_fee():
    assert core.fee_cents(datetime.fromisoformat("2026-10-24T15:30:00Z")) == 300  # 17:30 Berlin
    assert core.fee_cents(datetime.fromisoformat("2026-10-24T09:00:00Z")) == 200


def test_future_slot_holds_bay_only_at_start(c):
    slot = c.get("/api/bays/bay-1/slots").json()[2]
    r = c.post("/api/reservations", json={"bayId": "bay-1", "slotStart": slot["start"]}, headers=D1).json()
    assert r["state"] == "SCHEDULED" and r["feeCents"] == slot["feeCents"] and r["allowedActions"] == ["cancel"]
    assert r["slotStart"] == slot["start"] and r["graceDeadline"] == slot["end"]
    assert core.adapter.locks[LOCK]["arm"] != "raised"  # soft hold until the slot starts
    assert [x["available"] for x in c.get("/api/bays/bay-1/slots").json()][1:4] == [True, False, True]  # only its own slot

    db.execute("UPDATE reservations SET slot_start = ? WHERE id = ?", db.iso(db.now() - timedelta(seconds=1)), r["id"])
    core.start_due_slots()
    r2 = get(c, r).json()
    assert r2["state"] == "RESERVED" and r2["graceDeadline"] == slot["end"] and core.adapter.locks[LOCK]["arm"] == "raised"


def test_cancel_scheduled_makes_no_hardware_call(c):
    slot = c.get("/api/bays/bay-1/slots").json()[1]
    r = c.post("/api/reservations", json={"bayId": "bay-1", "slotStart": slot["start"]}, headers=D1).json()
    assert c.post(f"/api/reservations/{r['id']}/cancel", headers=D1).json()["state"] == "CANCELLED"
    assert not db.rows("SELECT 1 FROM event_log WHERE kind = 'adapter_call'")


def test_unknown_slot_rejected(c):
    r = c.post("/api/reservations", json={"bayId": "bay-1", "slotStart": "2020-01-01T00:00:00Z"}, headers=D1)
    assert r.status_code == 400 and r.json()["error"]["code"] == "bad_slot"


def test_second_driver_gets_other_slots_only(c):
    s = c.get("/api/bays/bay-1/slots").json()
    book = lambda slot, h: c.post("/api/reservations", json={"bayId": "bay-1", "slotStart": slot["start"]}, headers=h)
    assert book(s[1], D1).status_code == 201
    taken = book(s[1], D2)
    assert taken.status_code == 409 and taken.json()["error"]["code"] == "slot_taken"
    assert book(s[2], D2).json()["state"] == "SCHEDULED"  # back-to-back slot is fine
    assert c.get("/api/bays/bay-1").json()["status"] == "free"  # future bookings do not block walk-ins now


def test_now_booking_blocks_now_and_overlapping_slot_only(c):
    assert c.post("/api/reservations", json={"bayId": "bay-1"}, headers=D1).json()["state"] == "RESERVED"
    s = c.get("/api/bays/bay-1/slots").json()
    assert not s[0]["available"]
    assert s[-1]["available"]
