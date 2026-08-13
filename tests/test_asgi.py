"""Tests for the FastAPI ASGI assembly: health route + the mounted MCP app.

Uses FastAPI's `TestClient` as a context manager (not a bare
`httpx.ASGITransport`) because only the context-manager form actually runs
ASGI lifespan startup/shutdown -- and FastMCP's session manager depends on
that lifespan running. Skipping it produces a misleading "Task group not
initialized" error instead of this suite's explicit, intentional
assertions below.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.asgi import create_asgi_app
from app.config.settings import Settings
from app.server import create_server


def _client(settings: Settings | None = None) -> TestClient:
    settings = settings or Settings(_env_file=None, app_name="test-server", app_version="1.2.3")
    server = create_server(settings)
    return TestClient(create_asgi_app(server, settings))


def test_health_endpoint_reports_configured_name_and_version() -> None:
    with _client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "name": "test-server",
        "version": "1.2.3",
        "environment": "development",
    }


def test_mcp_endpoint_is_mounted_and_session_manager_is_running() -> None:
    # A request with no session ID gets a clean protocol-level 400 from
    # FastMCP's own session handling -- not a crash. Getting *this*
    # response (rather than "Task group is not initialized") is exactly
    # what proves the lifespan was wired through to the parent app; see
    # the module docstring.
    with _client() as client:
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 400
    assert "session" in response.json()["error"]["message"].lower()
