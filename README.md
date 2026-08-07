# mcp-tool-server

A production-ready [MCP](https://modelcontextprotocol.io/) tool server built with [FastMCP](https://gofastmcp.com).

**Status:** Phase 1 — Architecture & Project Initialization

## Stack

Python 3.12+ · FastMCP 3 · Pydantic v2 · uv

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
├── tools/          # MCP tools (empty — Phase 2)
├── services/       # Business logic behind tools (empty — Phase 2)
└── models/         # Pydantic schemas (empty — Phase 2)
tests/
└── test_bootstrap.py  # Smoke tests for the scaffold
```

## Testing

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Roadmap

- [x] Phase 1 — Architecture & project initialization
- [ ] Phase 2 — Example tools + tool metadata
- [ ] Phase 3 — FastAPI mounting + health endpoint
- [ ] Phase 4 — Full unit test suite
- [ ] Phase 5 — Docker + docker-compose
- [ ] Phase 6 — Full documentation pass
