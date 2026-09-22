"""
Every device mutation gets recorded here — including which "trust source"
triggered it. This is the instrument that will let later phases answer
"did the attack actually succeed, and through which channel" with a real
number instead of a guess.
"""
import time
from typing import List
from pydantic import BaseModel


class AuditEvent(BaseModel):
    timestamp: float
    device_id: str
    action: str
    params: dict = {}
    resulting_state: object
    source: str  # e.g. "chat", "device_webhook", "unknown"


_audit_log: List[AuditEvent] = []


def record_event(device_id: str, action: str, params: dict, resulting_state, source: str) -> AuditEvent:
    event = AuditEvent(
        timestamp=time.time(),
        device_id=device_id,
        action=action,
        params=params,
        resulting_state=resulting_state,
        source=source,
    )
    _audit_log.append(event)
    return event


def get_audit_log() -> List[AuditEvent]:
    return list(_audit_log)


def clear_audit_log() -> None:
    _audit_log.clear()
