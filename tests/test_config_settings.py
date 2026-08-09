"""Edge-case tests for application settings not covered by the bootstrap
smoke tests: environment-variable overrides, invalid values, and the
`is_production` convenience property.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_env_vars_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_APP_NAME", "from-env")
    monkeypatch.setenv("MCP_PORT", "9999")

    settings = Settings(_env_file=None)

    assert settings.app_name == "from-env"
    assert settings.port == 9999


def test_is_production_true_only_in_production_environment() -> None:
    assert Settings(_env_file=None, environment="production").is_production is True
    assert Settings(_env_file=None, environment="development").is_production is False
    assert Settings(_env_file=None, environment="staging").is_production is False


def test_invalid_environment_value_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="not-a-real-environment")


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, log_level="NOT_A_LEVEL")


def test_invalid_transport_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, transport="carrier-pigeon")
