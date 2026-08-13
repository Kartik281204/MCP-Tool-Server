"""Authentication/authorization for the MCP endpoint.

Kept as its own package (rather than folded into `utils/`) because it's a
distinct, security-relevant concern with its own testing and review needs.
"""

from app.security.api_key_auth import ApiKeyVerifier, build_auth_provider

__all__ = ["ApiKeyVerifier", "build_auth_provider"]
