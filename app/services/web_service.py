"""URL-metadata fetching logic, independent of the MCP transport.

Only transport-level failures (bad scheme, timeout, DNS, connection refused)
raise. HTTP error status codes (4xx/5xx) are returned as data -- a 404 is a
valid answer to "what does this URL return?", not a tool failure.
"""

from __future__ import annotations

import time

import httpx

from app.models.web import UrlMetadata

_ALLOWED_SCHEMES = {"http", "https"}


async def fetch_url_metadata(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    client: httpx.AsyncClient | None = None,
) -> UrlMetadata:
    """Fetch `url` and report its status, headers, and response time.

    Args:
        url: The URL to request. Only http/https schemes are allowed.
        timeout_seconds: Request timeout in seconds.
        client: Optional client override, primarily for tests (inject one
            built with `httpx.MockTransport` to avoid real network calls).

    Raises:
        ValueError: If the scheme is unsupported or the request cannot
            complete (timeout, DNS failure, connection refused, etc).
    """
    scheme = httpx.URL(url).scheme
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"unsupported URL scheme '{scheme}'; only http/https are allowed")

    owns_client = client is None
    client = client or httpx.AsyncClient()
    try:
        start = time.perf_counter()
        try:
            response = await client.get(url, timeout=timeout_seconds, follow_redirects=True)
        except httpx.HTTPError as exc:
            raise ValueError(f"failed to reach {url}: {exc}") from exc
        elapsed_ms = (time.perf_counter() - start) * 1000

        content_length = response.headers.get("content-length")
        return UrlMetadata(
            url=str(response.url),
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            content_length_bytes=int(content_length) if content_length is not None else None,
            response_time_ms=round(elapsed_ms, 2),
        )
    finally:
        if owns_client:
            await client.aclose()
