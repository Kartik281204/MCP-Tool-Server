"""Business logic and integrations, kept independent of the MCP transport.

Tools in `app.tools` should stay thin and delegate real work to services
defined here, so the logic is unit-testable without going through the MCP
protocol layer at all.
"""

from app.services.conversion_service import convert_temperature
from app.services.text_analysis_service import analyze_text
from app.services.web_service import fetch_url_metadata

__all__ = ["analyze_text", "convert_temperature", "fetch_url_metadata"]
