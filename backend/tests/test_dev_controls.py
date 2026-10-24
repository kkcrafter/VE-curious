from fastapi.testclient import TestClient

from app import core
from app.main import app


def test_dev_routes_play_s1_and_failures():
    with TestClient(app) as c:
        c.post("/api/dev/reset")
        token = c.post("/api/login", json={"email": "driver1@demo.test", "password": "demo1234"}).json()["token"]
        D1 = {"Authorization": "Bearer " + token}
        core.tick()
        c.post("/api/dev/fail-next", json={"call": "reserve"})
        assert c.post("/api/reservations", json={"bayId": "bay-1"}, headers=D1).status_code == 502
        r = c.post("/api/reservations", json={"bayId": "bay-1"}, headers=D1).json()

        c.post("/api/dev/camera", json={"bayId": "bay-1", "online": False})
        c.post("/api/dev/plate", json={"bayId": "bay-1", "plate": "M-AB 1234"})  # blind camera sees nothing
        assert c.get(f"/api/reservations/{r['id']}", headers=D1).json()["state"] == "RESERVED"

        c.post("/api/dev/camera", json={"bayId": "bay-1", "online": True})
        c.post("/api/dev/plate", json={"bayId": "bay-1", "plate": "M-AB 1234"})
        c.post("/api/reservations/{}/charging".format(r["id"]), json={"action": "start"}, headers=D1)
        c.post("/api/dev/presence", json={"bayId": "bay-1", "occupied": False})
        assert c.get(f"/api/reservations/{r['id']}", headers=D1).json()["state"] == "COMPLETED"

        c.post("/api/dev/reset")
        assert c.get("/api/me/reservations", headers=D1).status_code == 401  # reset also ends sessions
        token = c.post("/api/login", json={"email": "driver1@demo.test", "password": "demo1234"}).json()["token"]
        assert c.get("/api/me/reservations", headers={"Authorization": "Bearer " + token}).json() == []
