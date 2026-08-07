"""Pydantic models for the URL-metadata tool."""

from __future__ import annotations

from pydantic import BaseModel, Field


class UrlMetadata(BaseModel):
    """Metadata collected from a single HTTP GET request to a URL."""

    url: str = Field(description="The final URL after following redirects.")
    status_code: int = Field(description="HTTP status code returned by the server.")
    content_type: str | None = Field(
        default=None, description="Value of the Content-Type header, if present."
    )
    content_length_bytes: int | None = Field(
        default=None, description="Value of the Content-Length header, if present."
    )
    response_time_ms: float = Field(description="Round-trip time for the request, in milliseconds.")
