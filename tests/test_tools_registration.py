"""Integration-style tests confirming tools are wired onto the FastMCP
instance correctly -- not just callable as bare functions, but reachable
through `list_tools`/`call_tool` the way a real MCP client would use them.
"""

from __future__ import annotations

import pytest
from fastmcp.exceptions import ToolError

from app.config.settings import Settings
from app.server import create_server


@pytest.fixture
def server():
    return create_server(Settings(_env_file=None))


async def test_all_expected_tools_are_registered(server) -> None:
    tools = await server.list_tools()
    names = {tool.name for tool in tools}

    assert names == {"analyze_text", "fetch_url_metadata", "convert_temperature"}


async def test_analyze_text_tool_is_callable_through_the_server(server) -> None:
    result = await server.call_tool("analyze_text", {"text": "Hello there."})

    assert result.is_error is False
    assert result.structured_content["word_count"] == 2


async def test_convert_temperature_tool_is_callable_through_the_server(server) -> None:
    result = await server.call_tool(
        "convert_temperature", {"value": 0, "from_unit": "celsius", "to_unit": "fahrenheit"}
    )

    assert result.structured_content["output_value"] == 32


async def test_invalid_input_surfaces_as_a_tool_error(server) -> None:
    with pytest.raises(ToolError):
        await server.call_tool("analyze_text", {"text": "   "})
