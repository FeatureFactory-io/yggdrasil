"""
``python manage.py mcp_server`` — launch the FastMCP server.

Supports two transports (SAO.md §18.2):
  --transport stdio   : JSON-RPC over stdin/stdout (Claude Desktop, Cursor)
  --transport http    : HTTP+SSE on --host / --port (remote clients, Case B)

Stdout hygiene is applied before any other output when transport=stdio.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import ClassVar

from django.core.management.base import BaseCommand

logger = logging.getLogger("yggdrasil.mcp")

# FastMCP tools may touch the ORM from async context (SAO.md §18).
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


class Command(BaseCommand):
    """Launch the FastMCP server with the specified transport."""

    help = "Launch the FastMCP MCP server (stdio or HTTP+SSE)"
    # Keep stdio JSON-RPC clean — no Django system-check chatter (SAO.md §18.6).
    requires_system_checks: ClassVar[list[str]] = []

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
        transport = options["transport"]
        host = options["host"]
        port = options["port"]
        logger.info(
            "mcp_server.handle: entry | transport=%s host=%s port=%s",
            transport,
            host,
            port,
        )
        self._apply_stdout_hygiene(transport)
        self._bind_user_from_env_token()
        mcp = self._initialize()
        self._run(mcp, transport=transport, host=host, port=port)

    def _apply_stdout_hygiene(self, transport: str) -> None:
        """Redirect print/logging away from stdout for stdio transport."""
        if transport != "stdio":
            return
        from yggdrasil.mcp.server import redirect_print_to_stderr

        redirect_print_to_stderr()
        root = logging.getLogger()
        for handler in list(root.handlers):
            if (
                isinstance(handler, logging.StreamHandler)
                and not isinstance(handler, logging.FileHandler)
                and getattr(handler, "stream", None) is sys.stdout
            ):
                handler.stream = sys.stderr
        sys.stdout.flush()
        sys.stderr.flush()
        logger.info("mcp_server: stdout hygiene applied for stdio")

    def _bind_user_from_env_token(self) -> None:
        """
        If ``YGGDRASIL_TOKEN`` is set, authenticate and set MCP user context.

        Case A (local stdio) uses the PAT from the environment so tool calls
        run as the token owner (SAO.md §18.5).
        """
        import hashlib

        from yggdrasil.auth.models import PersonalAccessToken
        from yggdrasil.auth.services import TokenService
        from yggdrasil.mcp.server import set_current_user_id, set_token_scope

        raw = os.environ.get("YGGDRASIL_TOKEN", "").strip()
        if not raw:
            logger.info("mcp_server: no YGGDRASIL_TOKEN in env — user context unset")
            return
        user = TokenService().authenticate(raw)
        if user is None:
            logger.error("mcp_server: YGGDRASIL_TOKEN invalid — refusing to start")
            self.stderr.write(self.style.ERROR("Invalid YGGDRASIL_TOKEN"))
            raise SystemExit(1)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        scope = PersonalAccessToken.objects.values_list("scope", flat=True).get(
            token_hash=token_hash
        )
        set_current_user_id(user.pk)
        set_token_scope(scope)
        logger.info(
            "mcp_server: user context bound | user_pk=%s scope=%s",
            user.pk,
            scope,
        )

    def _initialize(self):
        """Create FastMCP singleton and return it."""
        from yggdrasil.mcp.server import get_mcp, initialize_mcp

        initialize_mcp()
        mcp = get_mcp()
        logger.info("mcp_server: FastMCP ready")
        return mcp

    def _run(self, mcp, *, transport: str, host: str, port: int) -> None:
        """Block on ``mcp.run`` until the process is terminated."""
        logger.info("mcp_server: calling mcp.run | transport=%s", transport)
        if transport == "stdio":
            mcp.run(transport="stdio", show_banner=False, log_level="ERROR")
        else:
            mcp.run(
                transport="http",
                host=host,
                port=port,
                show_banner=False,
                log_level="ERROR",
            )
        logger.info("mcp_server: mcp.run returned (unexpected)")
