import json

from fastapi.testclient import TestClient

from app import db
from app.main import app


def test_seeded_bays_and_unknown_camera_is_unverified():
    with TestClient(app) as c:
        db.reset()
        bays = c.get("/api/bays").json()
        assert [b["id"] for b in bays] == ["bay-1", "bay-2"]
        assert all(b["status"] == "unverified" for b in bays)  # never seen -> never "free"
        db.update("bays", "bay-1", last_seen_at=db.iso(db.now()))
        assert c.get("/api/bays/bay-1").json()["status"] == "free"
        assert c.get("/api/bays/nope").json() == {"error": {"code": "not_found", "message": "Bay nope not found"}}


def test_event_log_writer():
    db.init()
    db.log("test", "r_1", "bay-1", n=1)
    row = db.one("SELECT * FROM event_log ORDER BY id DESC")
    assert (row["kind"], row["reservation_id"], json.loads(row["payload"])) == ("test", "r_1", {"n": 1})
