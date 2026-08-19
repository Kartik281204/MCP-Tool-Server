# syntax=docker/dockerfile:1

# --- Builder ---------------------------------------------------------------
FROM python:3.12-slim AS builder

# Pinned to the uv version this project was developed and tested against
# (see .python-version / pyproject.toml), not :latest, for reproducibility.
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies before copying the rest of the source, so this
# (slow) layer only re-runs when the lockfile actually changes.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# --- Runtime -----------------------------------------------------------
FROM python:3.12-slim AS runtime

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Only the built venv and application code -- no uv, no lockfile, no tests,
# no dev dependencies.
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH" \
    MCP_HOST=0.0.0.0 \
    MCP_TRANSPORT=http \
    PYTHONUNBUFFERED=1
# MCP_PORT is deliberately NOT baked in here. app/config/settings.py
# already defaults port to 8000 with no env var at all, so this ENV would
# be pure redundancy in the common case -- and actively wrong on a
# platform like Railway, which assigns a port dynamically via a bare
# `PORT` var: since MCP_PORT takes precedence when both are present (see
# settings.py), a baked-in MCP_PORT=8000 here would silently shadow
# Railway's real port on every single deploy.

USER appuser
EXPOSE 8000

# No curl/wget in the slim image -- a stdlib one-liner avoids adding either
# just for this. Resolves the actual port the same way app/config/settings.py
# does (MCP_PORT, then PORT, then 8000) rather than hardcoding 8000 --
# otherwise this silently breaks for anyone overriding MCP_PORT, Railway's
# dynamic PORT included.
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os,sys,urllib.request; p=os.environ.get('MCP_PORT') or os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{p}/health', timeout=3).status == 200 else 1)"

CMD ["python", "-m", "app.server"]
