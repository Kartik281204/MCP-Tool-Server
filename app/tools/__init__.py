"""MCP tool definitions.

Each submodule builds a standalone `Tool` via `FunctionTool.from_function`
rather than decorating an existing `mcp` instance. That keeps tools fully
decoupled from `app.server` -- no circular import, and each tool function
is callable/testable on its own. `create_server()` wires `ALL_TOOLS` in at
construction time via `FastMCP(tools=...)`.
"""

from app.tools.conversion import convert_temperature_tool
from app.tools.text_analysis import analyze_text_tool
from app.tools.web import fetch_url_metadata_tool

ALL_TOOLS = [analyze_text_tool, fetch_url_metadata_tool, convert_temperature_tool]

__all__ = ["ALL_TOOLS"]
