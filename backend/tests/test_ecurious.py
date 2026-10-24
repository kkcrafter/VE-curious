from app import hardware_events


def test_sse_parse_accepts_live_and_documented_names():
    assert hardware_events.parse("lock:car_presence", {"lockId": "l", "presence": "occupied"})["occupied"] is True
    assert hardware_events.parse("vehicle_presence", {"lockId": "l", "presence": "vacant"})["occupied"] is False
    assert hardware_events.parse("lock:photo_captured", {"lockId": "l", "licensePlate": "AB1"})["plate"] == "AB1"
    assert hardware_events.parse("lock:status_changed", {"lockId": "l", "status": "raised"})["kind"] == "arm"
    assert hardware_events.parse("connected", {}) is None
