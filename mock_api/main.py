"""
A small, standalone, simulated smart-home device API. The agent talks to
this exactly the way it would talk to a real one — the separation is
deliberate, so the eventual security story is "can an agent be tricked
through a real tool boundary," not "can I break my own toy."
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from mock_api.devices_store import list_devices, get_device, set_device_state, reset_devices
from mock_api.audit_log import record_event, get_audit_log, clear_audit_log

app = FastAPI(title="Mock Smart Home API")


class ActionRequest(BaseModel):
    source: str = "unknown"


class SetTemperatureRequest(ActionRequest):
    value: float


@app.get("/devices")
def get_devices():
    return list_devices()


@app.get("/devices/{device_id}")
def get_device_status(device_id: str):
    try:
        return get_device(device_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="device not found")


def _mutate(device_id: str, action: str, new_state, params: dict, source: str):
    try:
        result = set_device_state(device_id, new_state)
    except KeyError:
        raise HTTPException(status_code=404, detail="device not found")
    record_event(device_id, action, params, result["state"], source)
    return result


@app.post("/devices/{device_id}/lock")
def lock_device(device_id: str, req: ActionRequest):
    return _mutate(device_id, "lock", "locked", {}, req.source)


@app.post("/devices/{device_id}/unlock")
def unlock_device(device_id: str, req: ActionRequest):
    return _mutate(device_id, "unlock", "unlocked", {}, req.source)


@app.post("/devices/{device_id}/toggle")
def toggle_device(device_id: str, req: ActionRequest):
    current = get_device(device_id)
    new_state = "off" if current["state"] == "on" else "on"
    return _mutate(device_id, "toggle", new_state, {}, req.source)


@app.post("/devices/{device_id}/set_temperature")
def set_temperature(device_id: str, req: SetTemperatureRequest):
    return _mutate(device_id, "set_temperature", req.value, {"value": req.value}, req.source)


@app.post("/devices/{device_id}/arm")
def arm_alarm(device_id: str, req: ActionRequest):
    return _mutate(device_id, "arm", "armed", {}, req.source)


@app.post("/devices/{device_id}/disarm")
def disarm_alarm(device_id: str, req: ActionRequest):
    return _mutate(device_id, "disarm", "disarmed", {}, req.source)


@app.get("/devices/{device_id}/snapshot")
def get_snapshot(device_id: str):
    device = get_device(device_id)
    if device["kind"] != "camera":
        raise HTTPException(status_code=400, detail="not a camera device")
    return {"device_id": device_id, "snapshot": "base64-placeholder-image-data"}


@app.get("/audit-log")
def audit_log():
    return get_audit_log()


@app.post("/reset")
def reset():
    """Test/attack-harness helper: reset devices and clear the audit log."""
    reset_devices()
    clear_audit_log()
    return {"status": "reset"}


@app.get("/health")
def health():
    return {"status": "ok"}
