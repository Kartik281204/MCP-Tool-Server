"""Tests for `main()`'s transport dispatch.

`main()` ends in a blocking call (`mcp.run()` or `uvicorn.run()`), so these
patch those calls out and assert on *how* they'd be invoked rather than
letting a server actually start.
"""

from __future__ import annotations

from unittest.mock import patch

from app.config.settings import Settings


def test_main_runs_stdio_transport_directly() -> None:
    settings = Settings(_env_file=None, transport="stdio")

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.mcp.run") as mock_run,
    ):
        from app.server import main

        main()

    mock_run.assert_called_once_with(transport="stdio")


def test_main_serves_http_transport_via_uvicorn() -> None:
    settings = Settings(_env_file=None, transport="http", host="127.0.0.1", port=9000)

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.asgi.create_asgi_app") as mock_create_app,
        patch("uvicorn.run") as mock_uvicorn_run,
    ):
        from app.server import main, mcp

        main()

    mock_create_app.assert_called_once_with(mcp, settings)
    mock_uvicorn_run.assert_called_once_with(
        mock_create_app.return_value, host="127.0.0.1", port=9000
    )
