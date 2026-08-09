"""ASGI app assembly for the `http` transport.

Only relevant when serving over HTTP. The `stdio` transport talks to a
client over stdin/stdout directly and never touches this module -- see
`app.server.main`.

FastMCP's own `mcp.run(transport="http")` is sufficient on its own, but it
only serves the MCP protocol endpoint. Mounting `mcp.http_app()` into a
FastAPI app instead lets us add plain REST routes -- today just `/health`
-- alongside it on the same port.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api import health_router
from app.config.settings import Settings, get_settings
from app.server import mcp

# FastMCP's session manager starts up via this sub-app's lifespan. It has to
# be handed to the *parent* FastAPI app's `lifespan=` -- FastAPI does not
# run a mounted sub-app's lifespan automatically -- or tool calls fail with
# session errors despite `/health` working fine.
_mcp_app = mcp.http_app(path="/mcp")


def create_asgi_app(settings: Settings) -> FastAPI:
    """Build the FastAPI app: health route + the MCP endpoint mounted at `/mcp`."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=_mcp_app.lifespan,
    )
    # Route handlers resolve settings via `Depends(get_settings)`, which
    # would otherwise ignore the `settings` passed in here and fall back to
    # the process-wide cached singleton. Overriding the dependency is what
    # makes the parameter above actually take effect (and is what makes
    # this app testable with settings other than the real environment's).
    app.dependency_overrides[get_settings] = lambda: settings
    app.include_router(health_router)
    app.mount("/", _mcp_app)
    return app
