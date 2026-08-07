"""Application configuration.

All runtime configuration is sourced from environment variables (or a local
``.env`` file) via a single cached ``Settings`` instance. Nothing in the rest
of the codebase should read ``os.environ`` directly -- go through
``get_settings()`` instead so configuration stays centralized and testable.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

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
    port: int = 8000

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
