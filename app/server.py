"""MCP server application factory and process entrypoint.

Phase 1 wires up the server shell only: configuration, logging, and a
named FastMCP instance with no tools registered yet. Tool registration
lands in Phase 2 (see app/tools/).
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from app.config.settings import Settings, get_settings
from app.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def create_server(settings: Settings | None = None) -> FastMCP:
    """Build a configured FastMCP server instance.

    Args:
        settings: Explicit settings to use instead of the cached global
            instance. Primarily intended for tests, which need isolated,
            deterministic configuration.

    Returns:
        A ``FastMCP`` instance named and versioned from settings, with
        logging configured as a side effect. No tools are registered yet.
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)
    logger.info(
        "server_initializing name=%s version=%s environment=%s transport=%s",
        resolved_settings.app_name,
        resolved_settings.app_version,
        resolved_settings.environment,
        resolved_settings.transport,
    )
    return FastMCP(name=resolved_settings.app_name, version=resolved_settings.app_version)


# Module-level instance so `fastmcp run app/server.py` and `uv run python -m
# app.server` both resolve the same configured server object.
mcp = create_server()


def main() -> None:
    """Run the MCP server using the transport configured in settings."""
    settings = get_settings()
    if settings.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=settings.transport, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
