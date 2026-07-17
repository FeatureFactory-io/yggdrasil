"""
``python manage.py mcp_server`` — launch the FastMCP server.

Supports two transports (SAO.md §18.2):
  --transport stdio   : JSON-RPC over stdin/stdout (Claude Desktop, Cursor)
  --transport http    : HTTP+SSE on --host / --port (remote clients, Case B)

Stdout hygiene is applied before any other output when transport=stdio.
"""

from __future__ import annotations

import logging

from django.core.management.base import BaseCommand

logger = logging.getLogger("yggdrasil.mcp")


class Command(BaseCommand):
    """Launch the FastMCP server with the specified transport."""

    help = "Launch the FastMCP MCP server (stdio or HTTP+SSE)"

    def add_arguments(self, parser) -> None:
        """
        :param parser: Django management command argument parser.
        """
        parser.add_argument(
            "--transport",
            default="stdio",
            choices=["stdio", "http"],
            help="Transport protocol. Default: stdio",
        )
        parser.add_argument(
            "--host",
            default="0.0.0.0",
            help="Host for HTTP+SSE transport. Default: 0.0.0.0",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=8001,
            help="Port for HTTP+SSE transport. Default: 8001",
        )

    def handle(self, *args, **options) -> None:
        """
        Start the FastMCP server.

        :param options: Parsed CLI arguments (transport, host, port).
        :raises SystemExit: On server error.
        """
        raise NotImplementedError()
