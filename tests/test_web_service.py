"""Unit tests for the URL-metadata service.

Uses httpx's built-in `MockTransport` (no extra dependency) so these tests
never make real network calls -- fast, deterministic, and independent of
network access in whatever environment runs them.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.web_service import fetch_url_metadata


async def test_fetch_url_metadata_parses_a_successful_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html", "content-length": "1234"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_url_metadata("https://example.com", client=client)

    assert result.status_code == 200
    assert result.content_type == "text/html"
    assert result.content_length_bytes == 1234
    assert result.response_time_ms >= 0


async def test_fetch_url_metadata_does_not_raise_on_http_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_url_metadata("https://example.com/missing", client=client)

    assert result.status_code == 404


async def test_fetch_url_metadata_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="scheme"):
        await fetch_url_metadata("ftp://example.com")


async def test_fetch_url_metadata_wraps_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="failed to reach"):
            await fetch_url_metadata("https://example.com", client=client)
