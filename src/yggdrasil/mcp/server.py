"""
FastMCP server singleton and initialisation (SAO.md §18 — MCP Architecture).

Integration case: Hybrid (Case A = in-process Django app + Case B = standalone
Dockerfile.mcp facade). Transport: stdio (local IDE) + HTTP+SSE (remote clients).

Stdout hygiene: ALL logging is routed to stderr so the stdio JSON-RPC channel
is never polluted. This is critical for Claude Desktop / Cursor compatibility.

Usage:
    # Case A — called once at Django startup (apps.py ready() hook):
    from yggdrasil.mcp.server import initialize_mcp
    initialize_mcp()

    # Case B — standalone entrypoint via management command:
    uv run python manage.py mcp_server --transport stdio
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

logger = logging.getLogger("yggdrasil.mcp")

# ─── Current-request user injected by auth middleware (SAO.md §18.5) ─────────
# Never accept user_id as a tool argument — always read from this ContextVar.
_current_user_id: ContextVar[int | None] = ContextVar("mcp_user_id", default=None)

_mcp_instance = None
_initialized = False


def get_mcp():
    """
    Return the FastMCP server singleton; raise if not initialised.

    :return: FastMCP server instance.
    :raises RuntimeError: If initialize_mcp() has not been called.
    """
    if _mcp_instance is None:
        raise RuntimeError("FastMCP server not initialised — call initialize_mcp() first")
    return _mcp_instance


def initialize_mcp() -> None:
    """
    Create the FastMCP singleton and register all tool modules.

    Idempotent — safe to call multiple times (no-op after first call).
    Called from MCP app's ``ready()`` hook so tools are available at startup.

    Registration order matters: tools are registered in module import order.
    All registration happens here so there is one canonical place to find
    every tool the server exposes.

    :raises ImportError: If fastmcp is not installed.
    """
    global _mcp_instance, _initialized
    if _initialized:
        logger.info("initialize_mcp | already initialised — no-op")
        return
    _ensure_stderr_logging()
    from fastmcp import FastMCP

    mcp = FastMCP("yggdrasil")
    _register_tools(mcp)
    _mcp_instance = mcp
    _initialized = True
    logger.info("initialize_mcp | FastMCP singleton ready")


def _ensure_stderr_logging() -> None:
    """
    Redirect root logger to stderr so stdout stays clean for JSON-RPC.

    Must be called before any FastMCP server startup (SAO.md §18.4 — stdout
    hygiene). Only applies when transport=stdio; HTTP+SSE uses normal logging.
    """
    root = logging.getLogger()
    for handler in list(root.handlers):
        if isinstance(handler, logging.StreamHandler) and handler.stream is sys.stdout:
            handler.stream = sys.stderr
    logger.debug("_ensure_stderr_logging | StreamHandlers pointing at stdout redirected")


def _register_tools(mcp) -> None:
    """
    Import and register each tool module against the FastMCP instance.

    Each sub-module in ``mcp/tools/`` calls ``@mcp.tool`` on its functions.
    Importing them here is sufficient for registration.
    """
    from yggdrasil.mcp.tools import changeset as changeset_tools
    from yggdrasil.mcp.tools import query as query_tools
    from yggdrasil.mcp.tools import write as write_tools

    query_fns = [
        query_tools.list_elements,
        query_tools.search,
        query_tools.get_element,
        query_tools.traverse,
        query_tools.list_changesets,
        query_tools.get_changeset,
        query_tools.list_stereotypes,
        query_tools.list_ratatosk_runs,
    ]
    changeset_fns = [
        changeset_tools.approve_changeset,
        changeset_tools.reject_changeset,
        changeset_tools.do_other_changeset,
        changeset_tools.ask_munin,
    ]
    write_fns = [
        write_tools.create_element,
        write_tools.update_element,
        write_tools.delete_element,
        write_tools.create_relationship,
        write_tools.update_relationships_batch,
        write_tools.set_model_mode,
    ]
    for fn in [*query_fns, *changeset_fns, *write_fns]:
        mcp.tool(fn)
        logger.info("_register_tools | registered %s", fn.__name__)


def get_current_user_id() -> int | None:
    """
    Return the authenticated user ID from the current MCP request context.

    :return: User PK or None if unauthenticated (should never be None in
        production — authentication middleware sets this before tool dispatch).
    """
    return _current_user_id.get()


def set_current_user_id(user_id: int | None) -> None:
    """
    Set the authenticated user ID for the current MCP request context.

    Called by MCP authentication middleware — not by tool implementations.

    :param user_id: Authenticated user PK. Example: 42
    """
    _current_user_id.set(user_id)
    logger.debug("mcp.server: user context set | user_id=%s", user_id)


def redirect_print_to_stderr() -> None:
    """
    Monkeypatch ``print`` to write to stderr during stdio MCP sessions.

    Prevents any accidental ``print()`` call from corrupting the JSON-RPC
    channel. Only called by the ``mcp_server`` management command.
    """
    import builtins

    _original_print = builtins.print

    def _safe_print(*args, **kwargs) -> None:
        kwargs.setdefault("file", sys.stderr)
        _original_print(*args, **kwargs)

    builtins.print = _safe_print  # type: ignore[assignment]
    logger.debug("mcp.server: print() redirected to stderr for stdio transport")
