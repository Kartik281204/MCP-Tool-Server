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


def test_api_key_set_parses_and_strips_comma_separated_keys() -> None:
    settings = Settings(_env_file=None, api_keys=" key-a ,key-b,, key-c")

    assert settings.api_key_set == frozenset({"key-a", "key-b", "key-c"})


def test_auth_disabled_by_default() -> None:
    assert Settings(_env_file=None).auth_enabled is False
    assert Settings(_env_file=None).api_key_set == frozenset()


def test_auth_enabled_when_any_key_configured() -> None:
    assert Settings(_env_file=None, api_keys="one-key").auth_enabled is True


def test_port_defaults_to_8000_with_neither_var_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("PORT", raising=False)

    assert Settings(_env_file=None).port == 8000


def test_port_falls_back_to_bare_port_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Railway (and Heroku) assign a port dynamically via a bare `PORT` env
    var with no `MCP_` prefix -- this is the fallback that makes the app
    actually reachable there instead of listening on the wrong port.
    """
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.setenv("PORT", "5555")

    assert Settings(_env_file=None).port == 5555


def test_mcp_port_takes_precedence_over_bare_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit MCP_PORT should win over a platform-injected PORT, same
    as every other setting in this class being explicitly overridable.
    """
    monkeypatch.setenv("MCP_PORT", "9999")
    monkeypatch.setenv("PORT", "5555")

    assert Settings(_env_file=None).port == 9999
