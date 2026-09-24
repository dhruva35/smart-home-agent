from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import requests
import logging
import os

from agent.agent import run_agent
from agent.pending import list_pending, approve_pending, deny_pending, reset_pending
from agent.config import settings

logger = logging.getLogger("api")

app = FastAPI(title="Smart Home Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all: always return JSON so the frontend never sees an HTML 500."""
    logger.exception("Unhandled error on %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "detail": "Internal server error — check server logs."},
    )


class ChatRequest(BaseModel):
    message: str


class WebhookRequest(BaseModel):
    event_text: str


# ------------------------------------------------------------------ #
#  UI                                                                  #
# ------------------------------------------------------------------ #

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve the frontend SPA."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# ------------------------------------------------------------------ #
#  Agent channels                                                      #
# ------------------------------------------------------------------ #

@app.post("/chat")
def chat(req: ChatRequest):
    """Trusted owner channel — commands execute directly."""
    try:
        answer = run_agent(source="owner_sms", user_text=req.message)
        return {"answer": answer}
    except Exception as exc:
        logger.exception("Agent error in /chat")
        return JSONResponse(
            status_code=200,  # Return 200 so the frontend still parses as JSON
            content={"answer": f"⚠️ Agent error: {exc}. Please check that GOOGLE_API_KEY and MOCK_API_URL are set correctly on Render."},
        )


@app.post("/webhook/device-event")
def device_event(req: WebhookRequest):
    """Untrusted webhook channel — the red-team attack surface."""
    try:
        answer = run_agent(source="device_webhook", user_text=req.event_text)
        return {"answer": answer}
    except Exception as exc:
        logger.exception("Agent error in /webhook/device-event")
        return JSONResponse(
            status_code=200,
            content={"answer": f"⚠️ Agent error: {exc}. Please check that GOOGLE_API_KEY and MOCK_API_URL are set correctly on Render."},
        )


# ------------------------------------------------------------------ #
#  HITL approval endpoints                                             #
# ------------------------------------------------------------------ #

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
    resp = requests.post(
        f"{settings.mock_api_url}/devices/{action.device_id}/{action.action}",
        json={"source": "owner_approved"},
    )
    resp.raise_for_status()
    return {"status": "approved", "result": resp.json()}


@app.post("/deny/{token}")
def deny(token: str):
    if not deny_pending(token):
        raise HTTPException(status_code=404, detail="Pending action not found or expired")
    return {"status": "denied"}


# ------------------------------------------------------------------ #
#  Proxy endpoints — the frontend talks to a single origin (port 8000) #
# ------------------------------------------------------------------ #

@app.get("/api/devices")
def proxy_devices():
    resp = requests.get(f"{settings.mock_api_url}/devices")
    resp.raise_for_status()
    return resp.json()


@app.get("/api/audit-log")
def proxy_audit_log():
    resp = requests.get(f"{settings.mock_api_url}/audit-log")
    resp.raise_for_status()
    return resp.json()


@app.post("/api/reset")
def proxy_reset():
    resp = requests.post(f"{settings.mock_api_url}/reset")
    resp.raise_for_status()
    reset_pending()
    return resp.json()


# ------------------------------------------------------------------ #
#  Static files — mount LAST so API routes take priority              #
# ------------------------------------------------------------------ #

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
