"""Pydantic model for the health endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Liveness status of the running server."""

    status: Literal["ok"] = "ok"
    name: str = Field(description="Configured application name.")
    version: str = Field(description="Configured application version.")
    environment: str = Field(description="Configured deployment environment.")
