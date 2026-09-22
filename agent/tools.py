"""
Builds the agent's tool set for a single invocation, bound to a fixed
`source` label ("owner_sms" or "device_webhook").

SECURITY INVARIANT (see tests/test_agent_tools.py): `source` is set by the
API layer that calls build_tools(), never exposed as a tool argument the
LLM could fill in itself. If the model could set its own trust label, the
whole audit trail would be worthless -- an attacker could just claim
"source: owner_sms" for an action that actually came from a webhook.
This is a one-line mistake to make and a very easy one to miss in review,
which is exactly why it has a dedicated regression test.

Phase 1(e) CHANNEL GUARDS: High-risk and privacy-sensitive tools now
enforce source == "owner_sms" in Python code before any API call is made.
The LLM cannot override this -- it is not a prompt instruction, it is a
branch in executable code. Untrusted channels (device_webhook, unknown)
are hard-blocked with an error string returned to the LLM.
"""
from typing import List

import requests
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent.config import settings
from agent.pending import create_pending


class DeviceIdInput(BaseModel):
    device_id: str = Field(description="The device identifier, e.g. 'front_door'")


class SetTemperatureInput(BaseModel):
    device_id: str = Field(description="The thermostat device id, e.g. 'thermostat'")
    value: float = Field(description="Target temperature in Celsius")


def _post(path: str, source: str, json_extra: dict = None) -> dict:
    payload = {"source": source, **(json_extra or {})}
    resp = requests.post(f"{settings.mock_api_url}{path}", json=payload, timeout=5)
    resp.raise_for_status()
    return resp.json()


def _get(path: str) -> dict:
    resp = requests.get(f"{settings.mock_api_url}{path}", timeout=5)
    resp.raise_for_status()
    return resp.json()


# Channels that are allowed to perform high-risk physical actions.
_TRUSTED_SOURCES = {"owner_sms"}


def _require_trusted(source: str, tool_name: str) -> str | None:
    """Return an error string if source is not trusted, else None.

    Usage inside a tool function:
        if err := _require_trusted(source, "unlock_door"):
            return {"error": err}
    """
    if source not in _TRUSTED_SOURCES:
        return (
            f"Unauthorized: '{tool_name}' can only be called from a trusted "
            f"owner channel (e.g. owner_sms). Current source '{source}' is not "
            f"permitted to perform this action."
        )
    return None


def build_tools(source: str) -> List[StructuredTool]:
    """Build the tool set for one agent invocation, bound to `source`."""

    def list_devices() -> dict:
        """List devices. From untrusted sources, return only count to prevent recon."""
        if source not in _TRUSTED_SOURCES:
            devices = _get("/devices")
            count = len(devices)
            kinds = list({v["kind"] for v in devices.values()})
            return {"info": f"{count} devices present.", "kinds": kinds}
        return _get("/devices")

    def get_device_status(device_id: str) -> dict:
        """Get device status. From untrusted sources, redact state to prevent probing."""
        info = _get(f"/devices/{device_id}")
        if source not in _TRUSTED_SOURCES:
            # Return only device type, not current state -- prevents alarm/door probing.
            return {"device_id": device_id, "kind": info.get("kind", "unknown")}
        return info

    def lock_door(device_id: str) -> dict:
        return _post(f"/devices/{device_id}/lock", source)

    def unlock_door(device_id: str) -> dict:
        if source not in _TRUSTED_SOURCES:
            create_pending("unlock", device_id, source)
            return {"status": "pending_approval", "message": "Request submitted. Owner will be notified."}
        return _post(f"/devices/{device_id}/unlock", source)

    def toggle_light(device_id: str) -> dict:
        # Low-risk: webhooks legitimately control lights.
        return _post(f"/devices/{device_id}/toggle", source)

    def set_thermostat(device_id: str, value: float) -> dict:
        # Low-risk: webhooks legitimately adjust temperature.
        return _post(f"/devices/{device_id}/set_temperature", source, {"value": value})

    def arm_alarm(device_id: str) -> dict:
        return _post(f"/devices/{device_id}/arm", source)

    def disarm_alarm(device_id: str) -> dict:
        if source not in _TRUSTED_SOURCES:
            create_pending("disarm", device_id, source)
            return {"status": "pending_approval", "message": "Request submitted. Owner will be notified."}
        return _post(f"/devices/{device_id}/disarm", source)

    def view_camera_snapshot(device_id: str) -> dict:
        if err := _require_trusted(source, "view_camera_snapshot"):
            # Generic error -- do not reveal device IDs or capability details.
            return {"error": "Access denied. This operation requires owner authorization."}
        return _get(f"/devices/{device_id}/snapshot")

    return [
        StructuredTool.from_function(
            func=list_devices, name="list_devices",
            description="List all smart home devices and their current state.",
        ),
        StructuredTool.from_function(
            func=get_device_status, name="get_device_status", args_schema=DeviceIdInput,
            description="Get the current state of one device.",
        ),
        StructuredTool.from_function(
            func=lock_door, name="lock_door", args_schema=DeviceIdInput,
            description="Lock a door device.",
        ),
        StructuredTool.from_function(
            func=unlock_door, name="unlock_door", args_schema=DeviceIdInput,
            description="Unlock a door device. Security-critical.",
        ),
        StructuredTool.from_function(
            func=toggle_light, name="toggle_light", args_schema=DeviceIdInput,
            description="Toggle a light device on/off.",
        ),
        StructuredTool.from_function(
            func=set_thermostat, name="set_thermostat", args_schema=SetTemperatureInput,
            description="Set the thermostat target temperature in Celsius.",
        ),
        StructuredTool.from_function(
            func=arm_alarm, name="arm_alarm", args_schema=DeviceIdInput,
            description="Arm the alarm system.",
        ),
        StructuredTool.from_function(
            func=disarm_alarm, name="disarm_alarm", args_schema=DeviceIdInput,
            description="Disarm the alarm system. Security-critical.",
        ),
        StructuredTool.from_function(
            func=view_camera_snapshot, name="view_camera_snapshot", args_schema=DeviceIdInput,
            description="View a snapshot from a camera device.",
        ),
    ]
