"""
In-process MCP tool client for Journey L1 / AT.

Calls the same Python tool functions registered on FastMCP — not LocalOrm
bypass, not HTTP. Sets auth ContextVar for the duration of each call.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools import propose as propose_tools
from yggdrasil.mcp.tools import query as query_tools

logger = logging.getLogger("yggdrasil.ratatosk.inprocess_mcp")

_TOOL_MAP: dict[str, Callable[..., dict]] = {
    "list_elements": query_tools.list_elements,
    "list_relationships": query_tools.list_relationships,
    "list_stereotypes": query_tools.list_stereotypes,
    "ensure_model": propose_tools.ensure_model,
    "propose_changeset": propose_tools.propose_changeset,
    "record_ratatosk_run": propose_tools.record_ratatosk_run,
}


class InProcessMcpToolClient:
    """
    Sync ``call_tool`` facade over registered MCP tool callables.

    Used by Journey L1 so discovery uses the real propose/list paths.
    """

    def __init__(self, *, user_id: int | None, token_scope: str = "read-write") -> None:
        """
        :param user_id: Django user PK injected into MCP ContextVar.
        :param token_scope: read-only or read-write.
        """
        self._user_id = user_id
        self._token_scope = token_scope

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Invoke a registered tool by name.

        :param name: Tool name. Example: ``"list_elements"``.
        :param arguments: Keyword args for the tool.
        :return: Tool result dict.
        :raises KeyError: If tool is not in the in-process map.
        """
        arguments = arguments or {}
        if name not in _TOOL_MAP:
            msg = f"Unknown in-process MCP tool: {name!r}"
            raise KeyError(msg)
        set_current_user_id(self._user_id)
        set_token_scope(self._token_scope)
        logger.info(
            "InProcessMcpToolClient.call_tool | tool=%s user_id=%s keys=%s",
            name,
            self._user_id,
            sorted(arguments.keys()),
        )
        result = _TOOL_MAP[name](**arguments)
        if not isinstance(result, dict):
            return {"value": result}
        return result
