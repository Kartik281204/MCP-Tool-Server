"""Tests for API-key authentication.

Split in two: unit tests against `ApiKeyVerifier`/`build_auth_provider`
directly, and integration tests that go through real HTTP with an actual
`Authorization` header. The in-memory `fastmcp.Client` transport can't
stand in for the latter -- it bypasses HTTP (and therefore headers/auth)
entirely, which is exactly what surfaced the `create_asgi_app` refactor
this test file exercises.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.asgi import create_asgi_app
from app.config.settings import Settings
from app.security.api_key_auth import ApiKeyVerifier, build_auth_provider
from app.server import create_server

# --- Unit tests --------------------------------------------------------


async def test_verifier_accepts_a_configured_key() -> None:
    verifier = ApiKeyVerifier(frozenset({"key-a", "key-b"}))

    token = await verifier.verify_token("key-b")

    assert token is not None
    assert token.token == "key-b"


async def test_verifier_rejects_an_unconfigured_key() -> None:
    verifier = ApiKeyVerifier(frozenset({"key-a"}))

    assert await verifier.verify_token("not-a-real-key") is None


async def test_verifier_rejects_empty_token_against_empty_key_set() -> None:
    verifier = ApiKeyVerifier(frozenset())

    assert await verifier.verify_token("anything") is None


def test_build_auth_provider_is_none_when_no_keys_configured() -> None:
    settings = Settings(_env_file=None, api_keys="")

    assert build_auth_provider(settings) is None


def test_build_auth_provider_returns_verifier_when_keys_configured() -> None:
    settings = Settings(_env_file=None, api_keys="a-key")

    provider = build_auth_provider(settings)

    assert isinstance(provider, ApiKeyVerifier)


# --- Integration tests (real HTTP, real headers) ------------------------


def _mcp_client(settings: Settings) -> TestClient:
    return TestClient(create_asgi_app(create_server(settings), settings))


def _initialize_body() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "0"},
        },
    }


def test_mcp_endpoint_rejects_requests_with_no_token_when_auth_enabled() -> None:
    settings = Settings(_env_file=None, api_keys="secret-key")

    with _mcp_client(settings) as client:
        response = client.post(
            "/mcp",
            json=_initialize_body(),
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 401


def test_mcp_endpoint_rejects_an_incorrect_token() -> None:
    settings = Settings(_env_file=None, api_keys="secret-key")

    with _mcp_client(settings) as client:
        response = client.post(
            "/mcp",
            json=_initialize_body(),
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer wrong-token",
            },
        )

    assert response.status_code == 401


def test_mcp_endpoint_accepts_a_correct_token() -> None:
    settings = Settings(_env_file=None, api_keys="key-one,secret-key")

    with _mcp_client(settings) as client:
        response = client.post(
            "/mcp",
            json=_initialize_body(),
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer secret-key",
            },
        )

    assert response.status_code == 200


def test_health_endpoint_is_not_gated_by_auth() -> None:
    settings = Settings(_env_file=None, api_keys="secret-key")

    with _mcp_client(settings) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_mcp_endpoint_has_no_auth_when_no_keys_configured() -> None:
    settings = Settings(_env_file=None, api_keys="")

    with _mcp_client(settings) as client:
        response = client.post(
            "/mcp",
            json=_initialize_body(),
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 200
