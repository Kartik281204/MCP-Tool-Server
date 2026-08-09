"""Health check endpoint.

Trivial enough (just echoing config back) that it stays inline here rather
than delegating to a service module. Revisit that call if this ever needs
to check a real downstream dependency (database, cache, etc.) -- at that
point a `/health/ready` readiness check, backed by its own service, would
be the right addition alongside this liveness check.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.config.settings import Settings, get_settings
from app.models.health import HealthStatus

router = APIRouter()


@router.get("/health", tags=["observability"])
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthStatus:
    """Report that the process is up and which build/environment it's running."""
    return HealthStatus(
        name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
