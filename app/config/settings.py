"""Application configuration.

All runtime configuration is sourced from environment variables (or a local
``.env`` file) via a single cached ``Settings`` instance. Nothing in the rest
of the codebase should read ``os.environ`` directly -- go through
``get_settings()`` instead so configuration stays centralized and testable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

TransportName = Literal["stdio", "http", "sse"]
Environment = Literal["development", "staging", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Typed application settings, validated at process startup.

    Values are read from environment variables prefixed with ``MCP_`` (e.g.
    ``MCP_LOG_LEVEL``), falling back to a local ``.env`` file if present.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore",
        # `port` below has an explicit validation_alias; without this,
        # pydantic v2 stops accepting the plain field name as a
        # constructor kwarg for that field, breaking `Settings(port=...)`
        # everywhere the test suite (and anything else) constructs
        # Settings directly rather than through the environment.
        populate_by_name=True,
    )

    app_name: str = "mcp-tool-server"
    app_version: str = "0.1.0"
    environment: Environment = "development"
    log_level: LogLevel = "INFO"

    # Transport for the MCP server itself. "stdio" is used when a client
    # spawns this process directly; "http" runs it as a standalone network
    # service, which is what the Docker deployment (a later phase) expects.
    transport: TransportName = "http"
    host: str = "0.0.0.0"
    # Some PaaS platforms (Railway, Heroku) assign a port dynamically and
    # inject it as a bare `PORT` env var the app is expected to bind --
    # there's no way to rename that on their end, so it's accepted here as
    # a fallback. `MCP_PORT` wins if both happen to be set, so an explicit
    # override still behaves exactly like every other setting in this
    # class. Fly/Cloud Run/Kubernetes all use a fixed, developer-chosen
    # port instead and are unaffected by this either way.
    port: int = Field(default=8000, validation_alias=AliasChoices("MCP_PORT", "PORT"))

    # Comma-separated bearer tokens for the MCP endpoint. Empty (the
    # default) disables auth entirely -- deliberately open out of the box
    # so `uv run python -m app.server` keeps working with zero setup. Set
    # this before exposing the server anywhere it isn't fully trusted.
    api_keys: str = ""

    @property
    def api_key_set(self) -> frozenset[str]:
        """Parsed, non-empty API keys."""
        return frozenset(key.strip() for key in self.api_keys.split(",") if key.strip())

    @property
    def auth_enabled(self) -> bool:
        """Whether any API key is configured. See `api_keys` above."""
        return bool(self.api_key_set)

    @property
    def is_production(self) -> bool:
        """Whether the server is running in the production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide cached ``Settings`` instance.

    Cached with ``lru_cache`` so settings are parsed once and reused as a
    singleton, matching the standard FastAPI dependency-injection pattern.
    """
    return Settings()
