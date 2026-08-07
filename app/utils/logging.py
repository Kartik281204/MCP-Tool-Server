"""Logging configuration for the MCP tool server.

Kept deliberately on the standard library (no structlog/loguru dependency)
since a plain formatter satisfies today's requirements; revisit only if a
concrete need for structured JSON logs emerges (e.g. a log-aggregation
pipeline that requires it).
"""

from __future__ import annotations

import logging
import sys

from app.config.settings import Settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def configure_logging(settings: Settings) -> None:
    """Configure root logging handlers and level from application settings.

    Idempotent: safe to call multiple times (e.g. across test runs) because
    ``force=True`` replaces any handlers installed by a previous call.
    """
    logging.basicConfig(
        level=settings.log_level,
        format=_LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )
