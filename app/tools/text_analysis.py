"""MCP tool wrapping the text-analysis service."""

from __future__ import annotations

from fastmcp.exceptions import ToolError
from fastmcp.tools import FunctionTool
from mcp.types import ToolAnnotations

from app.models.text_analysis import TextAnalysisResult
from app.services.text_analysis_service import analyze_text as _analyze_text


def analyze_text(text: str) -> TextAnalysisResult:
    """Compute word, character, and sentence counts plus an estimated reading time.

    Args:
        text: The text to analyze. Must be non-empty.
    """
    try:
        return _analyze_text(text)
    except ValueError as exc:
        raise ToolError(str(exc)) from exc


analyze_text_tool = FunctionTool.from_function(
    analyze_text,
    tags={"text", "utility"},
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
