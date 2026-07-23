"""Tests for RatatoskMcpClient HTTP tool calls."""

from __future__ import annotations

import httpx
import pytest

from yggdrasil.ratatosk.mcp_client import McpClientError, RatatoskMcpClient


def test_call_tool_posts_bearer_and_unwraps_result() -> None:
    """Successful tool call sends Bearer auth and returns result dict."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/mcp/tools/list_elements"
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json={"result": {"items": [{"name": "Payment API"}], "total": 1}},
        )

    transport = httpx.MockTransport(handler)
    client = RatatoskMcpClient(
        server="https://yggdrasil.example",
        token="test-token",
        transport=transport,
    )
    result = client.call_tool("list_elements", {"model": "yggdrasil"})
    assert result["total"] == 1
    assert result["items"][0]["name"] == "Payment API"


def test_call_tool_401_raises_mcp_error() -> None:
    """401 from MCP becomes McpClientError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="unauthorized")

    client = RatatoskMcpClient(
        server="https://yggdrasil.example",
        token="bad",
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(McpClientError, match="authentication"):
        client.call_tool("list_elements", {"model": "yggdrasil"})
