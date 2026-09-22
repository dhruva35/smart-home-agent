"""
In-memory "digital twin" of a small smart home. No real hardware involved —
this is the safe, resettable environment the agent acts on, so red-team runs
in later phases can be repeated exactly and measured precisely.
"""
from typing import Dict

_DEFAULT_DEVICES: Dict[str, dict] = {
    "front_door": {"kind": "lock", "state": "locked"},
    "back_door": {"kind": "lock", "state": "locked"},
    "living_room_light": {"kind": "light", "state": "off"},
    "thermostat": {"kind": "thermostat", "state": 21},
    "alarm_system": {"kind": "alarm", "state": "armed"},
    "camera_front": {"kind": "camera", "state": "ok"},
}

_devices: Dict[str, dict] = {k: dict(v) for k, v in _DEFAULT_DEVICES.items()}


def list_devices() -> Dict[str, dict]:
    return {k: dict(v) for k, v in _devices.items()}


def get_device(device_id: str) -> dict:
    if device_id not in _devices:
        raise KeyError(device_id)
    return dict(_devices[device_id])


def set_device_state(device_id: str, new_state) -> dict:
    if device_id not in _devices:
        raise KeyError(device_id)
    _devices[device_id]["state"] = new_state
    return dict(_devices[device_id])


def reset_devices() -> None:
    """Reset every device to its default safe state.

    Call this between red-team runs so each attack attempt starts from the
    same known-good baseline instead of compounding on a previous attack.
    """
    global _devices
    _devices = {k: dict(v) for k, v in _DEFAULT_DEVICES.items()}
