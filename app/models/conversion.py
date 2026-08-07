"""Pydantic models and types for the temperature-conversion tool."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TemperatureUnit = Literal["celsius", "fahrenheit", "kelvin"]


class ConversionResult(BaseModel):
    """Result of converting a temperature from one unit to another."""

    input_value: float
    input_unit: TemperatureUnit
    output_value: float = Field(description="`input_value` converted to `output_unit`.")
    output_unit: TemperatureUnit
