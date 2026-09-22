from fastapi.testclient import TestClient

from mock_api.main import app
from mock_api.devices_store import reset_devices
from mock_api.audit_log import clear_audit_log

client = TestClient(app)


def setup_function():
    reset_devices()
    clear_audit_log()


def test_list_devices():
    resp = client.get("/devices")
    assert resp.status_code == 200
    assert "front_door" in resp.json()


def test_front_door_starts_locked():
    resp = client.get("/devices/front_door")
    assert resp.json()["state"] == "locked"


def test_unlock_door_changes_state_and_is_audited():
    resp = client.post("/devices/front_door/unlock", json={"source": "test"})
    assert resp.status_code == 200
    assert resp.json()["state"] == "unlocked"

    events = client.get("/audit-log").json()
    assert any(
        e["device_id"] == "front_door" and e["action"] == "unlock" and e["source"] == "test"
        for e in events
    )


def test_unknown_device_returns_404():
    resp = client.get("/devices/nonexistent")
    assert resp.status_code == 404


def test_reset_restores_locked_state_and_clears_log():
    client.post("/devices/front_door/unlock", json={"source": "test"})
    client.post("/reset")

    assert client.get("/devices/front_door").json()["state"] == "locked"
    assert client.get("/audit-log").json() == []
