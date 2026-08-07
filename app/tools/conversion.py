"""MCP tool wrapping the temperature-conversion service."""

from __future__ import annotations

from fastmcp.exceptions import ToolError
from fastmcp.tools import FunctionTool
from mcp.types import ToolAnnotations

from app.models.conversion import ConversionResult, TemperatureUnit
from app.services.conversion_service import convert_temperature as _convert_temperature


def convert_temperature(
    value: float,
    from_unit: TemperatureUnit,
    to_unit: TemperatureUnit,
) -> ConversionResult:
    """Convert a temperature between celsius, fahrenheit, and kelvin.

    Args:
        value: The temperature value to convert.
        from_unit: Unit of `value`.
        to_unit: Unit to convert to.
    """
    try:
        converted = _convert_temperature(value, from_unit, to_unit)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc
    return ConversionResult(
        input_value=value,
        input_unit=from_unit,
        output_value=converted,
        output_unit=to_unit,
    )


convert_temperature_tool = FunctionTool.from_function(
    convert_temperature,
    tags={"math", "utility"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
