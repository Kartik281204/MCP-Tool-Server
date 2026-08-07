"""MCP tool wrapping the URL-metadata service."""

from __future__ import annotations

from fastmcp.exceptions import ToolError
from fastmcp.tools import FunctionTool
from mcp.types import ToolAnnotations

from app.models.web import UrlMetadata
from app.services.web_service import fetch_url_metadata as _fetch_url_metadata


async def fetch_url_metadata(url: str, timeout_seconds: float = 10.0) -> UrlMetadata:
    """Fetch a URL and report its status code, content type/length, and response time.

    Does not raise on HTTP error status codes (4xx/5xx) -- those come back as
    data, since a 404 is a valid answer to "what does this URL return?". Only
    transport-level failures (timeout, DNS, connection refused, bad scheme)
    raise.

    Args:
        url: The http/https URL to check.
        timeout_seconds: Request timeout in seconds.
    """
    try:
        return await _fetch_url_metadata(url, timeout_seconds=timeout_seconds)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


fetch_url_metadata_tool = FunctionTool.from_function(
    fetch_url_metadata,
    tags={"network", "utility"},
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
