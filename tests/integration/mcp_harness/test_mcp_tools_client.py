"""
T1 — FastMCP in-process Client (SAO.md §18.7 / artifact 57 §7).

Proves tools are registered and listed through the MCP protocol layer,
not just as bare Python functions.
"""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client

from yggdrasil.mcp import server as mcp_server_mod


@pytest.fixture(autouse=True)
def _reset_mcp_singleton():
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False
    yield
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False


@pytest.mark.django_db
def test_t1_tools_list_via_fastmcp_client():
    """Client.list_tools() returns the registered Yggdrasil tool set."""

    async def _run() -> set[str]:
        mcp_server_mod.initialize_mcp()
        mcp = mcp_server_mod.get_mcp()
        async with Client(mcp) as client:
            tools = await client.list_tools()
        return {t.name for t in tools}

    names = asyncio.run(_run())
    assert "list_elements" in names
    assert "list_relationships" in names
    assert "propose_changeset" in names
    assert "record_ratatosk_run" in names
    assert "list_stereotypes" in names
    assert "ask_munin" in names
    assert "update_element" in names
    assert len(names) == 22
