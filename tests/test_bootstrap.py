"""Smoke tests for Phase 1: confirm the scaffold initializes correctly.

Behavioral tests for individual tools land alongside them in later phases;
this module only proves the application shell boots.
"""

from __future__ import annotations

from fastmcp import FastMCP

from app.config.settings import Settings, get_settings
from app.server import create_server


def test_settings_load_with_defaults() -> None:
    """Settings should resolve to documented defaults with no env/​.env file."""
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.app_name == "mcp-tool-server"
    assert settings.environment == "development"
    assert settings.transport == "http"
    assert settings.port == 8000


def test_get_settings_returns_a_cached_singleton() -> None:
    """get_settings() should return the same instance across calls."""
    assert get_settings() is get_settings()


def test_create_server_uses_provided_settings() -> None:
    """create_server() should name/version the FastMCP instance from settings."""
    settings = Settings(_env_file=None, app_name="test-server", app_version="9.9.9")  # type: ignore[call-arg]

    server = create_server(settings)

    assert isinstance(server, FastMCP)
    assert server.name == "test-server"
    assert server.version == "9.9.9"
