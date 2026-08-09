"""REST-facing routes, separate from the MCP tool layer in `app.tools`.

Small today (just health), but this is where any future plain-HTTP surface
(webhooks, admin routes, etc.) belongs -- kept apart from the MCP protocol
endpoint mounted alongside it in `app.asgi`.
"""

from app.api.health import router as health_router

__all__ = ["health_router"]
