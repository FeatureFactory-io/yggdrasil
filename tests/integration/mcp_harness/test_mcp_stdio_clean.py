"""
T3 — Subprocess stdio via FastMCP Client (SAO.md §18.7 / artifact 57 §7).

Proves the real Cursor entrypoint:
  uv run python manage.py mcp_server --transport stdio
boots, speaks MCP over stdio, and lists tools. No mocks.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports.stdio import StdioTransport

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_mcp_server_stdio_entrypoint_lists_tools():
    """
    Spawn ``manage.py mcp_server --transport stdio`` and list tools over MCP.

    If stdout is polluted or ``handle`` is still a stub, Client connect fails.
    """

    async def _run() -> set[str]:
        env = {k: v for k, v in os.environ.items() if k != "YGGDRASIL_TOKEN"}
        env.setdefault("DJANGO_SETTINGS_MODULE", "yggdrasil.settings")
        env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

        transport = StdioTransport(
            command="uv",
            args=["run", "python", "manage.py", "mcp_server", "--transport", "stdio"],
            cwd=str(REPO_ROOT),
            env=env,
            keep_alive=False,
        )
        async with Client(transport) as client:
            tools = await client.list_tools()
        return {t.name for t in tools}

    names = asyncio.run(_run())
    assert "list_elements" in names
    assert "update_element" in names
    assert "ask_munin" in names
    assert len(names) == 23
    assert "list_packages" in names
