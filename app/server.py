"""MCP server application factory and process entrypoint.

The tool registry (`app.tools.ALL_TOOLS`) is wired into the FastMCP
instance at construction time. See app/tools/__init__.py for why tools are
built standalone rather than via an `@mcp.tool` decorator.
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from app.config.settings import Settings, get_settings
from app.security import build_auth_provider
from app.tools import ALL_TOOLS
from app.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def create_server(settings: Settings | None = None) -> FastMCP:
    """Build a configured FastMCP server instance with all tools registered.

    Args:
        settings: Explicit settings to use instead of the cached global
            instance. Primarily intended for tests, which need isolated,
            deterministic configuration.

    Returns:
        A ``FastMCP`` instance named and versioned from settings, with
        every tool in ``app.tools.ALL_TOOLS`` already registered and, if
        ``settings.auth_enabled``, bearer-token auth required to call them.
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)
    auth_provider = build_auth_provider(resolved_settings)
    logger.info(
        "server_initializing name=%s version=%s environment=%s transport=%s tools=%d auth=%s",
        resolved_settings.app_name,
        resolved_settings.app_version,
        resolved_settings.environment,
        resolved_settings.transport,
        len(ALL_TOOLS),
        "enabled" if auth_provider else "disabled",
    )
    return FastMCP(
        name=resolved_settings.app_name,
        version=resolved_settings.app_version,
        tools=ALL_TOOLS,
        auth=auth_provider,
    )


# Module-level instance so `fastmcp run app/server.py` and `uv run python -m
# app.server` both resolve the same configured server object.
mcp = create_server()


def main() -> None:
    """Run the MCP server using the transport configured in settings.

    `stdio` runs FastMCP directly. `http` serves the FastAPI app (health
    route + the MCP endpoint mounted alongside it) via uvicorn instead of
    calling `mcp.run()` directly, so both are reachable on one port.
    """
    settings = get_settings()
    if settings.transport == "stdio":
        mcp.run(transport="stdio")
        return

    import uvicorn

    from app.asgi import create_asgi_app

    uvicorn.run(create_asgi_app(mcp, settings), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
