"""Static API-key bearer-token verification for the MCP endpoint.

Deliberately simple: a `TokenVerifier` (resource-server pattern, no OAuth
flow) checking against a configured set of pre-shared keys. Appropriate for
a small number of known/trusted callers -- not a substitute for real
OAuth/OIDC if this server ever needs per-user identity or third-party
client registration. `fastmcp.server.auth.providers` bundles Auth0, WorkOS,
GitHub, and others for that case; reach for one of those rather than
extending this class.

Deliberately does *not* protect `/health` -- infrastructure checking
liveness (Docker's HEALTHCHECK, a load balancer, a k8s probe) shouldn't
need credentials just to know the process is up. Only `create_server()`
receives this provider; `app.api.health` is never touched by it.
"""

from __future__ import annotations

import hmac

from fastmcp.server.auth import AccessToken, TokenVerifier

from app.config.settings import Settings


class ApiKeyVerifier(TokenVerifier):
    """Accepts a bearer token if and only if it's in the configured key set."""

    def __init__(self, valid_keys: frozenset[str]) -> None:
        super().__init__()
        self._valid_keys = valid_keys

    async def verify_token(self, token: str) -> AccessToken | None:
        # Constant-time comparison against each configured key, rather than
        # a plain `token in self._valid_keys` membership check, so a valid
        # key can't be inferred faster via response-timing side channels.
        if not any(hmac.compare_digest(token, key) for key in self._valid_keys):
            return None
        return AccessToken(token=token, client_id="api-key-client", scopes=[])


def build_auth_provider(settings: Settings) -> ApiKeyVerifier | None:
    """Return a configured verifier, or `None` if no keys are configured.

    `None` is a valid, first-class value here: `FastMCP(auth=None)` means
    "no auth", which is the deliberate default -- see `Settings.api_keys`.
    """
    if not settings.auth_enabled:
        return None
    return ApiKeyVerifier(settings.api_key_set)
