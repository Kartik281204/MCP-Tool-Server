# mcp-tool-server

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Tests](https://img.shields.io/badge/tests-32%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A production-shaped [MCP](https://modelcontextprotocol.io/) tool server built
with [FastMCP](https://gofastmcp.com) 3, FastAPI, and Pydantic v2 — three
example tools, a REST health endpoint on the same port, 100% test coverage,
and a multi-stage Docker build.

Built in six incremental phases (each independently reviewable in the commit
history this structure implies); see [Roadmap](#roadmap).

## Why this exists

This is a reference/portfolio implementation, not a business application —
the three tools exist to demonstrate patterns (sync vs. async execution,
external I/O, structured validation, error translation, tool metadata)
rather than to solve one specific problem. The interesting parts are the
architectural decisions, documented inline as comments where they're
non-obvious rather than collected in one wall of text here:

- **Tools are decoupled from the MCP server instance.** Each tool in
  `app/tools/` builds a standalone `Tool` via `FunctionTool.from_function(...)`
  instead of decorating an existing `mcp` object. `create_server()` wires
  them in at construction time (`FastMCP(tools=ALL_TOOLS)`). This avoids a
  circular import between `app.server` and `app.tools`, and makes every tool
  callable and unit-testable without any MCP machinery involved.
- **Business logic doesn't know MCP exists.** `app/services/` has zero
  FastMCP imports and raises plain `ValueError`. Translation to `ToolError`
  happens once, at the `app/tools/` boundary — the one place that's actually
  MCP-specific.
- **Dependencies were added when first used, not upfront.** FastAPI wasn't
  added until Phase 3, when the health endpoint actually needed it; `httpx`
  and `uvicorn` likewise. The result is a lockfile with nothing unused in it.
- **Two ASGI apps, one port.** `mcp.http_app()` returns a Starlette app for
  the MCP protocol; it's mounted inside a FastAPI app that also serves
  `/health`. The one genuine gotcha here — FastMCP's session manager needs
  the sub-app's `lifespan` explicitly passed to the *parent* app, or tool
  calls fail with a task-group error despite `/health` working fine — is
  documented where it's handled, in `app/asgi.py`.

## Tools

| Tool | Style | Tags | Description |
| --- | --- | --- | --- |
| `analyze_text` | sync | `text`, `utility` | Word/character/sentence counts and an estimated reading time. |
| `fetch_url_metadata` | async | `network`, `utility` | Status code, headers, and response time for an http/https URL. Only transport failures raise — a 404 is valid data. |
| `convert_temperature` | sync | `math`, `utility` | Convert between celsius, fahrenheit, and kelvin; rejects values below absolute zero. |

Each carries MCP tool annotations (`readOnlyHint`, `idempotentHint` /
`openWorldHint`) so clients can reason about side effects before calling them.

## Architecture

```
app/
├── server.py       # create_server(): builds the FastMCP instance + tool registry
├── asgi.py         # create_asgi_app(): mounts FastMCP into FastAPI for the http transport
├── config/         # Environment-driven settings (Pydantic v2 / pydantic-settings)
├── utils/          # Logging and other cross-cutting helpers
├── api/            # Plain REST routes (currently just /health)
├── tools/          # MCP tool adapters: schema, metadata, ValueError -> ToolError translation
├── services/       # Pure business logic. No FastMCP import, anywhere.
└── models/         # Pydantic schemas shared by tools/services/api
tests/              # 32 tests, 100% line coverage (unit + integration, no real network calls)
```

Dependency direction is one-way: `server`/`asgi` → `tools`/`api` → `services` → `models`.
Nothing in `services/` or `models/` imports anything above it.

## Quick Start

```bash
uv sync
cp .env.example .env
uv run python -m app.server
```

This starts the `http` transport on `http://0.0.0.0:8000`, serving both
`/health` and the MCP endpoint at `/mcp`. Set `MCP_TRANSPORT=stdio` in `.env`
instead if a client (e.g. Claude Desktop) will spawn this process directly.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The image is a multi-stage build (`python:3.12-slim` + pinned `uv`): dependencies
are synced in a builder stage from the lockfile before any application code is
copied in, so rebuilds only reinstall packages when `uv.lock` actually changes.
The runtime stage carries only the built virtual environment and `app/` — no
`uv`, no lockfile, no tests, no dev dependencies — and runs as a non-root user
with a `HEALTHCHECK` against `/health`.

```bash
# without compose
docker build -t mcp-tool-server .
docker run --rm -p 8000:8000 --env-file .env -e MCP_HOST=0.0.0.0 mcp-tool-server
```

> **Note:** the Dockerfile follows the standard multi-stage `uv` pattern and
> was reviewed carefully, but this environment had no Docker daemon available
> to actually run `docker build` against — unlike the rest of this project,
> it wasn't executed end-to-end. Worth a first build-and-run before you rely
> on it.

## Configuration

All variables are optional and prefixed `MCP_`; see `.env.example` for the
full, commented list. The ones worth knowing about:

| Variable | Default | Notes |
| --- | --- | --- |
| `MCP_TRANSPORT` | `http` | `stdio` for direct process spawning, `http` for a network service |
| `MCP_HOST` / `MCP_PORT` | `0.0.0.0` / `8000` | Only used for the `http` transport |
| `MCP_ENVIRONMENT` | `development` | `development` \| `staging` \| `production` |
| `MCP_LOG_LEVEL` | `INFO` | Standard library log level name |
| `FASTMCP_CHECK_FOR_UPDATES` | `stable` | FastMCP pings PyPI on startup by default; set `off` in production |

## Example usage

**Health check:**

```bash
curl http://localhost:8000/health
# {"status":"ok","name":"mcp-tool-server","version":"0.1.0","environment":"development"}
```

**Calling a tool** — the MCP endpoint is a stateful, session-based protocol
(not plain REST), so the practical way to call it is `fastmcp`'s own client
rather than raw curl:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "convert_temperature",
            {"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"},
        )
        print(result.data)  # output_value=212.0 ...

asyncio.run(main())
```

Or in-memory, against the server object directly (no network at all — this
is exactly what the test suite does):

```python
from fastmcp import Client
from app.server import mcp

async with Client(mcp) as client:
    tools = await client.list_tools()
```

## Testing

```bash
uv run pytest              # 32 tests, coverage report on by default (see pyproject.toml)
uv run ruff check .
uv run mypy app
```

Coverage is 100% across all 217 statements in `app/`. That number is a
byproduct of testing real behavior (every tool's error path, the settings
validation, the `main()` transport dispatch, the FastAPI lifespan wiring),
not a target chased for its own sake — the last few percentage points came
directly from `pytest --cov-report=term-missing` pointing at genuine gaps,
including one real bug it caught: `create_asgi_app(settings)` accepted a
`settings` argument that the health route was silently ignoring in favor of
the global cached singleton, fixed via a FastAPI dependency override in
`app/asgi.py`.

Network-dependent tests (`test_web_service.py`) use `httpx.MockTransport` —
no real HTTP calls, no flakiness, no dependency on network access in
whatever environment runs the suite.

## Roadmap

- [x] Phase 1 — Architecture & project initialization
- [x] Phase 2 — Example tools + tool metadata
- [x] Phase 3 — FastAPI mounting + health endpoint
- [x] Phase 4 — Full unit test suite
- [x] Phase 5 — Docker + docker-compose
- [x] Phase 6 — Full documentation pass

## License

MIT — see [LICENSE](LICENSE).
