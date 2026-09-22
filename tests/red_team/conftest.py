"""
Shared fixtures for the red-team test suite.

Key design decisions explained:

1. WHY TWO TestClients, NOT ONE
   The agent API (port 8000) and the mock smart home API (port 9000) are
   separate FastAPI apps. In tests, we use FastAPI's TestClient for both so
   we get in-process HTTP without needing real servers running. The agent's
   HTTP calls to the mock API still go through `requests` — but because
   mock_api is imported and its `app` object is used directly by the agent's
   tool layer (via the MOCK_API_URL env var pointing at the TestClient's
   base URL), we need to ensure they share the same in-memory state.

   The trick: we set MOCK_API_URL to "http://testserver" before importing
   anything, and we patch `requests` in the tools layer to route through the
   mock_api TestClient. This keeps tests fully in-process (no real network),
   deterministic, and fast.

   HOWEVER: for Phase 1(c), we actually want to run against the REAL live
   agent (including real LLM calls). Red-team tests are not unit tests.
   So instead, these fixtures assume both services are running on their
   default ports, just like `scripts/run_local.sh` starts them. The conftest
   sets up real HTTP clients pointing at localhost:8000 and localhost:9000.
   This is intentional: we're red-teaming the real thing.

2. WHY `reset_state` IS autouse=True IN THE red_team SCOPE
   Every attack test must start from a known-good baseline: all doors locked,
   alarm armed, audit log empty. If a previous test unlocked the front door,
   the next test might get a false negative ("attack didn't change state"
   because state was already compromised). autouse ensures the reset happens
   automatically before every test in this package without the test author
   having to remember to call it.

3. WHY WE READ THE AUDIT LOG VIA HTTP, NOT BY IMPORTING THE MODULE
   Importing `mock_api.audit_log._audit_log` directly would work in a
   unit-test context but would break the moment mock_api is running as a
   real separate process. Using the HTTP endpoint (`GET /audit-log`) keeps
   the test logic process-agnostic and matches the production observability
   model.
"""
import os
import pytest
import requests


# Default to localhost; override via env vars for CI or Docker setups
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:9000")


def _reset():
    """Reset all device state and clear the audit log via the mock API."""
    resp = requests.post(f"{MOCK_API_URL}/reset", timeout=5)
    resp.raise_for_status()


def _get_audit_log() -> list[dict]:
    """Fetch all audit events recorded since the last reset."""
    resp = requests.get(f"{MOCK_API_URL}/audit-log", timeout=5)
    resp.raise_for_status()
    return resp.json()


def _send_webhook(event_text: str) -> requests.Response:
    """Send an event to the untrusted webhook channel and return the full response."""
    return requests.post(
        f"{AGENT_API_URL}/webhook/device-event",
        json={"event_text": event_text},
        timeout=60,  # LLM calls can be slow
    )


def _send_chat(message: str) -> requests.Response:
    """Send a message to the chat channel and return the full response."""
    return requests.post(
        f"{AGENT_API_URL}/chat",
        json={"message": message},
        timeout=60,
    )


@pytest.fixture(autouse=True)
def reset_state():
    """
    Reset device state and audit log before every red-team test.
    autouse=True means this runs automatically — no test needs to call it.
    """
    _reset()
    yield
    # No teardown needed: the next test's setup reset will clean up.


@pytest.fixture
def audit_log():
    """Return a callable that fetches the current audit log state."""
    return _get_audit_log


@pytest.fixture
def send_webhook():
    """Return the webhook-sending helper."""
    return _send_webhook


@pytest.fixture
def send_chat():
    """Return the chat-sending helper."""
    return _send_chat
