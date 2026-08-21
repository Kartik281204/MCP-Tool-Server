"""URL-metadata fetching logic, independent of the MCP transport.

Only transport-level failures (bad scheme, blocked destination, timeout,
DNS, connection refused) raise. HTTP error status codes (4xx/5xx) are
returned as data -- a 404 is a valid answer to "what does this URL
return?", not a tool failure.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from collections.abc import Awaitable, Callable

import httpx

from app.models.web import UrlMetadata

_ALLOWED_SCHEMES = {"http", "https"}

AddressResolver = Callable[[str], Awaitable[list[str]]]


async def _default_resolve(hostname: str) -> list[str]:
    """Resolve `hostname` to its IP addresses via real DNS."""
    loop = asyncio.get_event_loop()
    try:
        results = await loop.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve host '{hostname}': {exc}") from exc
    return [str(sockaddr[0]) for _family, _type, _proto, _canonname, sockaddr in results]


def _is_public_address(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Whether `ip` is safe to let this server connect to on a caller's behalf."""
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def _reject_non_public_targets(hostname: str, resolve: AddressResolver) -> None:
    """Raise ValueError if `hostname` resolves to a private/internal address.

    This is a tool an AI agent calls with a caller/model-supplied URL --
    exactly the shape of an SSRF vector (e.g. pointing it at a cloud
    metadata endpoint like 169.254.169.254, or at this server's own
    internal network) if the destination isn't restricted to the public
    internet. Blocking by scheme alone (the only check here previously)
    does nothing to stop that; resolving the hostname and checking the
    actual address is what does.

    `resolve` is injected (default: real DNS via `_default_resolve`) for
    the same reason `fetch_url_metadata`'s `client` param is: tests need
    to exercise this exact resolution-and-check path without depending on
    real DNS being reachable from wherever the suite happens to run.

    Deliberately scoped to *this* check, not a fully general SSRF defense:
    it closes the direct case (a private/reserved IP, or a hostname that
    resolves to one, right now) but does not defend against DNS rebinding
    (a hostname resolving to a public IP here and a private one at actual
    connection time, moments later) -- that needs enforcement at the
    transport/socket layer, not a pre-check like this one.
    """
    for ip_str in await resolve(hostname):
        ip = ipaddress.ip_address(ip_str)
        if not _is_public_address(ip):
            raise ValueError(
                f"'{hostname}' resolves to a non-public address ({ip}); refusing to fetch"
            )


async def fetch_url_metadata(
    url: str,
    *,
    timeout_seconds: float = 10.0,
    client: httpx.AsyncClient | None = None,
    resolve: AddressResolver = _default_resolve,
) -> UrlMetadata:
    """Fetch `url` and report its status, headers, and response time.

    Args:
        url: The URL to request. Only http/https schemes are allowed, and
            only to hosts that resolve to a public address.
        timeout_seconds: Request timeout in seconds.
        client: Optional client override, primarily for tests (inject one
            built with `httpx.MockTransport` to avoid real network calls).
        resolve: Optional resolver override, primarily for tests (inject a
            fake one to avoid real DNS lookups).

    Raises:
        ValueError: If the scheme is unsupported, the host resolves to a
            private/internal address, or the request cannot complete
            (timeout, DNS failure, connection refused, etc).
    """
    parsed = httpx.URL(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"unsupported URL scheme '{parsed.scheme}'; only http/https are allowed")
    await _reject_non_public_targets(parsed.host, resolve)

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
