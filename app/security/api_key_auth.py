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
import logging

from fastmcp.server.auth import AccessToken, TokenVerifier

from app.config.settings import Settings

logger = logging.getLogger(__name__)

# Below this length, even a short prefix reveals too large a fraction of
# the token to be meaningfully safer than showing nothing.
_MIN_LENGTH_FOR_PARTIAL_REVEAL = 8
_VISIBLE_PREFIX_CHARS = 4


def mask_token(token: str) -> str:
    """Mask a token for safe logging: a short prefix and a length, no more.

    Never reveals enough to narrow a brute-force search or let two log
    lines be correlated back to the same key by a reader who doesn't
    already have it. This is the *only* form a submitted or configured
    token should ever take in a log line anywhere in this codebase.
    """
    if len(token) <= _MIN_LENGTH_FOR_PARTIAL_REVEAL:
        return "***"
    return f"{token[:_VISIBLE_PREFIX_CHARS]}...({len(token)} chars)"


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
            # WARNING, not DEBUG: a failed auth attempt is security-relevant
            # (could be a stale client, a typo, or a scan) and should be
            # visible at whatever level production actually runs at.
            logger.warning("api_key_auth_failed token=%s", mask_token(token))
            return None
        # DEBUG, not INFO: this fires on every successful call and would be
        # noisy at a level production typically runs at.
        logger.debug("api_key_auth_succeeded token=%s", mask_token(token))
        return AccessToken(token=token, client_id="api-key-client", scopes=[])


def build_auth_provider(settings: Settings) -> ApiKeyVerifier | None:
    """Return a configured verifier, or `None` if no keys are configured.

    `None` is a valid, first-class value here: `FastMCP(auth=None)` means
    "no auth", which is the deliberate default -- see `Settings.api_keys`.
    """
    if not settings.auth_enabled:
        return None
    return ApiKeyVerifier(settings.api_key_set)
