"""Business logic and integrations, kept independent of the MCP transport.

Tools in `app.tools` should stay thin and delegate real work to services
defined here, so the logic is unit-testable without going through the MCP
protocol layer at all.
"""
