"""
Thin MCP HTTP client for the Ratatosk CLI (snapshot + optional write tools).

Uses Bearer token auth against ``--server``. No Django ORM access — CLI is a
remote client for model reads (ACT-6-CICD-03 / ACT-1-DISC-13).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("ratatosk.mcp_client")


class McpClientError(RuntimeError):
    """Raised when an MCP tool call fails (network, auth, or protocol)."""


class RatatoskMcpClient:
    """
    Call Yggdrasil MCP tools over HTTP.

    Endpoint convention (FastMCP HTTP bridge):
    ``POST {server}/mcp/tools/{tool_name}`` with JSON ``{"arguments": {...}}``
    and ``Authorization: Bearer <token>``.
    """

    def __init__(
        self,
        server: str,
        token: str,
        *,
        timeout: float = 180.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        """
        :param server: Base Yggdrasil / MCP server URL.
        :param token: Personal access token (Bearer).
        :param timeout: HTTP timeout seconds.
        :param transport: Optional httpx transport (tests inject MockTransport).
        """
        self._server = server.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._transport = transport
        logger.info("RatatoskMcpClient: initialised | server=%s", self._server)

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Invoke an MCP tool by name.

        :param name: Tool name. Example: ``"list_elements"``.
        :param arguments: Tool arguments. Example: ``{"model": "yggdrasil"}``.
        :return: Tool result as a dict (unwraps ``{"result": ...}`` when present).
        :raises McpClientError: On HTTP or auth failure.
        """
        arguments = arguments or {}
        url = f"{self._server}/mcp/tools/{name}"
        logger.info(
            "RatatoskMcpClient.call_tool | tool=%s url=%s keys=%s",
            name,
            url,
            sorted(arguments.keys()),
        )
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.post(
                    url,
                    json={"arguments": arguments},
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Accept": "application/json",
                        "Content-Type": "application/json",
                    },
                )
        except httpx.HTTPError as exc:
            msg = f"MCP unreachable for tool {name!r}: {exc}"
            logger.error("RatatoskMcpClient.call_tool | %s", msg)
            raise McpClientError(msg) from exc

        if response.status_code in {401, 403}:
            msg = f"MCP authentication failed for tool {name!r} (HTTP {response.status_code})"
            logger.error("RatatoskMcpClient.call_tool | %s", msg)
            raise McpClientError(msg)
        if response.status_code >= 400:
            msg = f"MCP tool {name!r} failed: HTTP {response.status_code} {response.text[:200]}"
            logger.error("RatatoskMcpClient.call_tool | %s", msg)
            raise McpClientError(msg)

        try:
            payload = response.json()
        except ValueError as exc:
            msg = f"MCP tool {name!r} returned non-JSON body"
            raise McpClientError(msg) from exc

        if isinstance(payload, dict) and "result" in payload:
            result = payload["result"]
            if isinstance(result, dict):
                self._log_tool_result(name, result)
                return result
            return {"value": result}
        if isinstance(payload, dict):
            self._log_tool_result(name, payload)
            return payload
        return {"value": payload}

    def _log_tool_result(self, name: str, result: dict[str, Any]) -> None:
        """Log a concise summary of MCP tool results."""
        if "items" in result:
            total = result.get("total", len(result.get("items") or []))
            logger.info(
                "RatatoskMcpClient.call_tool | result tool=%s items=%s total=%s",
                name,
                len(result.get("items") or []),
                total,
            )
            return
        if "changeset_id" in result:
            logger.info(
                "RatatoskMcpClient.call_tool | result tool=%s changeset_id=%s operations=%s pending=%s",
                name,
                result.get("changeset_id"),
                result.get("operations_count"),
                result.get("pending_count"),
            )
            return
        if "slug" in result:
            logger.info(
                "RatatoskMcpClient.call_tool | result tool=%s slug=%s",
                name,
                result.get("slug"),
            )
            return
        logger.info(
            "RatatoskMcpClient.call_tool | result tool=%s keys=%s",
            name,
            sorted(result.keys()),
        )
