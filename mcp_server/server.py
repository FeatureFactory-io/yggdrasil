"""FastMCP server — thin wrapper over Yggdrasil REST API."""

from __future__ import annotations

import os

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("yggdrasil")

API_URL = os.environ.get("YGGDRASIL_API_URL", "http://localhost:8000/api/v1")


def _get(path: str, params: dict | None = None) -> dict:
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        resp = client.get(path, params=params or {})
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def search_elements(name: str = "") -> str:
    """Search elements by name in the live graph."""
    data = _get("/elements/", params={"search": name} if name else {})
    return str(data)


@mcp.tool()
def traverse_graph(from_id: int, depth: int = 3) -> str:
    """Traverse the graph from an element ID."""
    data = _get("/traverse/", params={"from_id": from_id, "depth": depth})
    return str(data)


if __name__ == "__main__":
    mcp.run()
