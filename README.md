# mcp-tool-server

A production-ready [MCP](https://modelcontextprotocol.io/) tool server built with [FastMCP](https://gofastmcp.com).

**Status:** Phase 2 — Example Tools & Tool Metadata

## Stack

Python 3.12+ · FastMCP 3 · Pydantic v2 · httpx · uv

## Tools

| Tool | Tags | Description |
| --- | --- | --- |
| `analyze_text` | `text`, `utility` | Word/character/sentence counts and an estimated reading time. |
| `fetch_url_metadata` | `network`, `utility` | Status code, headers, and response time for an http/https URL. |
| `convert_temperature` | `math`, `utility` | Convert between celsius, fahrenheit, and kelvin. |

Each tool is a thin adapter over a service function in `app/services/` —
the services have no FastMCP import and are unit-tested directly; the tool
layer only adds MCP-facing concerns (schema, metadata, error translation).

## Quick Start

```bash
uv sync
cp .env.example .env
uv run python -m app.server
```

The server starts on `http://0.0.0.0:8000` using the `http` transport by
default. Set `MCP_TRANSPORT=stdio` in `.env` if a client will spawn this
process directly instead of connecting over the network.

## Project Structure

```
app/
├── server.py       # FastMCP instance + process entrypoint
├── config/         # Environment-driven settings (Pydantic v2)
├── utils/          # Logging and other cross-cutting helpers
├── tools/          # MCP tool adapters (schema, metadata, error translation)
├── services/       # Pure business logic behind each tool, no FastMCP import
└── models/         # Pydantic schemas for tool inputs/outputs
tests/
├── test_bootstrap.py           # Scaffold smoke tests
├── test_tools_registration.py  # Tools reachable via list_tools/call_tool
├── test_text_analysis_service.py
├── test_conversion_service.py
└── test_web_service.py         # Uses httpx.MockTransport, no real network
```

## Testing

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Roadmap

- [x] Phase 1 — Architecture & project initialization
- [x] Phase 2 — Example tools + tool metadata
- [ ] Phase 3 — FastAPI mounting + health endpoint
- [ ] Phase 4 — Full unit test suite
- [ ] Phase 5 — Docker + docker-compose
- [ ] Phase 6 — Full documentation pass
