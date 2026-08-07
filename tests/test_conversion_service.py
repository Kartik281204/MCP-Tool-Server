"""Unit tests for the temperature-conversion service."""

from __future__ import annotations

import pytest

from app.services.conversion_service import convert_temperature


def test_celsius_to_fahrenheit() -> None:
    assert convert_temperature(0, "celsius", "fahrenheit") == 32


def test_celsius_to_kelvin() -> None:
    assert convert_temperature(0, "celsius", "kelvin") == pytest.approx(273.15)


def test_fahrenheit_to_celsius() -> None:
    assert convert_temperature(212, "fahrenheit", "celsius") == pytest.approx(100)


def test_same_unit_is_identity() -> None:
    assert convert_temperature(42, "kelvin", "kelvin") == 42


def test_rejects_temperature_below_absolute_zero() -> None:
    with pytest.raises(ValueError, match="absolute zero"):
        convert_temperature(-1, "kelvin", "celsius")
