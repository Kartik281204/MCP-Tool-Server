"""Unit tests for the URL-metadata service.

Uses httpx's built-in `MockTransport` (no extra dependency) for the HTTP
layer, and a fake `resolve` for the DNS layer -- both injected the same
way, both for the same reason: no real network call, of any kind,
anywhere in this file. A real hostname resolving successfully here would
prove nothing except that DNS happened to work in whatever environment
ran the suite; the resolver fake is what actually exercises the
resolution-and-check code path deterministically.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.web_service import _default_resolve, fetch_url_metadata

# example.com's real public IP -- confirmed directly against ipaddress'
# own classification (not RFC1918/loopback/link-local/reserved) before
# relying on it here, same as the blocked ranges below.
_PUBLIC_IP = "93.184.216.34"


async def _fake_public_resolver(_hostname: str) -> list[str]:
    return [_PUBLIC_IP]


async def test_fetch_url_metadata_parses_a_successful_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/html", "content-length": "1234"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_url_metadata(
            "https://example.com", client=client, resolve=_fake_public_resolver
        )

    assert result.status_code == 200
    assert result.content_type == "text/html"
    assert result.content_length_bytes == 1234
    assert result.response_time_ms >= 0


async def test_fetch_url_metadata_does_not_raise_on_http_error_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_url_metadata(
            "https://example.com/missing", client=client, resolve=_fake_public_resolver
        )

    assert result.status_code == 404


async def test_fetch_url_metadata_rejects_non_http_scheme() -> None:
    with pytest.raises(ValueError, match="scheme"):
        await fetch_url_metadata("ftp://example.com", resolve=_fake_public_resolver)


async def test_fetch_url_metadata_wraps_transport_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="failed to reach"):
            await fetch_url_metadata(
                "https://example.com", client=client, resolve=_fake_public_resolver
            )


async def test_fetch_url_metadata_creates_and_closes_its_own_client_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When no client is injected, the function should build (and clean up)
    its own -- this covers that path without making a real network call, by
    forcing every internally-constructed AsyncClient onto a MockTransport.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    real_init = httpx.AsyncClient.__init__

    def patched_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
        kwargs["transport"] = httpx.MockTransport(handler)
        real_init(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)

    result = await fetch_url_metadata("https://example.com", resolve=_fake_public_resolver)

    assert result.status_code == 200


# --- SSRF protection ------------------------------------------------------


@pytest.mark.parametrize(
    "blocked_ip",
    [
        "169.254.169.254",  # cloud instance metadata (AWS/GCP/Azure)
        "127.0.0.1",  # loopback
        "10.0.0.5",  # RFC1918 private
        "172.16.0.1",  # RFC1918 private
        "192.168.1.1",  # RFC1918 private
        "::1",  # IPv6 loopback
        "fc00::1",  # IPv6 unique local
    ],
)
async def test_fetch_url_metadata_blocks_hosts_resolving_to_non_public_addresses(
    blocked_ip: str,
) -> None:
    async def resolver(_hostname: str) -> list[str]:
        return [blocked_ip]

    with pytest.raises(ValueError, match="non-public address"):
        await fetch_url_metadata("https://internal.example", resolve=resolver)


async def test_fetch_url_metadata_allows_a_genuinely_public_address() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await fetch_url_metadata(
            "https://example.com", client=client, resolve=_fake_public_resolver
        )

    assert result.status_code == 200


async def test_fetch_url_metadata_blocked_host_never_reaches_the_http_client() -> None:
    """The SSRF check has to run *before* any request is attempted -- assert
    that directly rather than trust it, by wiring a client that fails the
    test if it's ever called at all.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("HTTP client was reached; SSRF check should have blocked this first")

    async def resolver(_hostname: str) -> list[str]:
        return ["127.0.0.1"]

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="non-public"):
            await fetch_url_metadata("https://internal.example", client=client, resolve=resolver)


async def test_fetch_url_metadata_wraps_dns_resolution_failures() -> None:
    async def resolver(hostname: str) -> list[str]:
        raise ValueError(f"could not resolve host '{hostname}': [simulated failure]")

    with pytest.raises(ValueError, match="could not resolve"):
        await fetch_url_metadata("https://does-not-exist.invalid", resolve=resolver)


# --- _default_resolve itself -----------------------------------------
#
# Everything above injects a fake resolver deliberately, to keep this file
# free of real DNS. These two are the intentional exception: they test
# `_default_resolve` directly (not through `fetch_url_metadata`) because
# it's the one piece of `fetch_url_metadata`'s own real behavior that a
# fake resolver can never exercise. Both targets are chosen specifically
# to stay network-independent regardless: `localhost` resolves via
# /etc/hosts rather than a real DNS round-trip, and `.invalid` is reserved
# by RFC 2606 to never resolve, so the failure path doesn't depend on
# reaching a real, possibly-unreachable-from-CI DNS server either.


async def test_default_resolve_returns_loopback_for_localhost() -> None:
    ips = await _default_resolve("localhost")

    assert "127.0.0.1" in ips


async def test_default_resolve_wraps_a_real_dns_failure() -> None:
    with pytest.raises(ValueError, match="could not resolve"):
        await _default_resolve("this-definitely-does-not-exist.invalid")
