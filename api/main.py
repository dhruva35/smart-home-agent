from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

from agent.agent import run_agent
from agent.pending import list_pending, approve_pending, deny_pending
from agent.config import settings

app = FastAPI(title="Smart Home Agent API")


class ChatRequest(BaseModel):
    message: str


class WebhookRequest(BaseModel):
    event_text: str


@app.post("/chat")
def chat(req: ChatRequest):
    """Trusted-ish channel: a person talking to their own smart home assistant."""
    answer = run_agent(source="chat", user_text=req.message)
    return {"answer": answer}


@app.post("/webhook/device-event")
def device_event(req: WebhookRequest):
    """
    Untrusted-ish channel: a simulated device/notification event (e.g. a
    doorbell press or delivery notice). This is the indirect-injection
    surface a later phase will red-team — right now the agent reacts to it
    exactly the same way it reacts to a trusted chat message, on purpose.
    Every resulting tool call still gets tagged "device_webhook" in the
    audit log, so the gap is measurable later even though it isn't
    defended against yet.
    """
    answer = run_agent(source="device_webhook", user_text=req.event_text)
    return {"answer": answer}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/pending")
def get_pending_actions():
    return list_pending()


@app.post("/approve/{token}")
def approve(token: str):
    action = approve_pending(token)
    if not action:
        raise HTTPException(status_code=404, detail="Pending action not found or expired")
    
    # Execute the action on behalf of the owner
    resp = requests.post(
        f"{settings.mock_api_url}/devices/{action.device_id}/{action.action}",
        json={"source": "owner_approved"}
    )
    resp.raise_for_status()
    return {"status": "approved", "result": resp.json()}


@app.post("/deny/{token}")
def deny(token: str):
    if not deny_pending(token):
        raise HTTPException(status_code=404, detail="Pending action not found or expired")
    return {"status": "denied"}
