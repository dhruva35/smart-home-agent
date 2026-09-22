import time
import uuid
from typing import Dict, Optional, List
from pydantic import BaseModel

class PendingAction(BaseModel):
    token: str
    action: str
    device_id: str
    source: str
    status: str = "pending"
    expires_at: float

_pending_store: Dict[str, PendingAction] = {}

def create_pending(action: str, device_id: str, source: str) -> str:
    """Create a new pending action and return its unique token."""
    token = uuid.uuid4().hex[:8]
    _pending_store[token] = PendingAction(
        token=token,
        action=action,
        device_id=device_id,
        source=source,
        expires_at=time.time() + 300  # 5 minutes
    )
    return token

def get_pending(token: str) -> Optional[PendingAction]:
    """Retrieve a pending action if it exists and hasn't expired."""
    action = _pending_store.get(token)
    if action and action.status == "pending" and time.time() < action.expires_at:
        return action
    return None

def approve_pending(token: str) -> Optional[PendingAction]:
    """Mark a pending action as approved and return it."""
    action = get_pending(token)
    if action:
        action.status = "approved"
        return action
    return None

def deny_pending(token: str) -> bool:
    """Mark a pending action as denied."""
    action = get_pending(token)
    if action:
        action.status = "denied"
        return True
    return False

def list_pending() -> List[dict]:
    """List all currently pending and unexpired actions."""
    now = time.time()
    return [
        a.dict() for a in _pending_store.values() 
        if a.status == "pending" and a.expires_at > now
    ]

def reset_pending() -> None:
    """Clear all pending actions (useful for tests)."""
    _pending_store.clear()
