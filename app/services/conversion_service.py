"""Pure temperature-conversion logic, independent of the MCP transport."""

from __future__ import annotations

from app.models.conversion import TemperatureUnit

_ABSOLUTE_ZERO_C = -273.15


def _to_celsius(value: float, unit: TemperatureUnit) -> float:
    if unit == "celsius":
        return value
    if unit == "fahrenheit":
        return (value - 32) * 5 / 9
    return value - 273.15  # kelvin


def _from_celsius(value_celsius: float, unit: TemperatureUnit) -> float:
    if unit == "celsius":
        return value_celsius
    if unit == "fahrenheit":
        return value_celsius * 9 / 5 + 32
    return value_celsius + 273.15  # kelvin


def convert_temperature(
    value: float, from_unit: TemperatureUnit, to_unit: TemperatureUnit
) -> float:
    """Convert `value` from `from_unit` to `to_unit`.

    Raises:
        ValueError: If `value` is below absolute zero in `from_unit`.
    """
    celsius = _to_celsius(value, from_unit)
    if celsius < _ABSOLUTE_ZERO_C - 1e-9:
        raise ValueError(f"{value} {from_unit} is below absolute zero ({_ABSOLUTE_ZERO_C}\u00b0C)")
    return round(_from_celsius(celsius, to_unit), 4)
