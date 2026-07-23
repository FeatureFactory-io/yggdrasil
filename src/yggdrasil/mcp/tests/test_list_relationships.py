"""Tests for MCP list_relationships (T1 + T2)."""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import Client
from tests.fixtures.factories.model_factories import (
    EdgeStereotypeFactory,
    ElementFactory,
    PackageFactory,
    RelationshipFactory,
    StereotypeFactory,
    YggdrasilModelFactory,
)

from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.mcp import server as mcp_server_mod
from yggdrasil.mcp.tools.query import list_relationships


@pytest.fixture(autouse=True)
def _reset_mcp_singleton():
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False
    yield
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False


@pytest.mark.django_db
def test_list_relationships_returns_total() -> None:
    """T2: model with N relationships → total + items."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    st = StereotypeFactory(metamodel=mm, name="Container", slug="container", is_edge=False)
    pkg = PackageFactory(metamodel=mm, name="Technology", slug="technology")
    a = ElementFactory(model=model, name="A", slug="a", stereotype=st, package=pkg)
    b = ElementFactory(model=model, name="B", slug="b", stereotype=st, package=pkg)
    edge = EdgeStereotypeFactory(metamodel=mm, name="depends_on", slug="depends_on")
    RelationshipFactory(model=model, source=a, target=b, stereotype=edge)
    RelationshipFactory(model=model, source=b, target=a, stereotype=edge)

    result = list_relationships(model="yggdrasil", limit=50)
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["stereotype_slug"] == "depends_on"


@pytest.mark.django_db
def test_list_relationships_mcp_client() -> None:
    """T1: tool registered and callable via FastMCP Client."""

    async def _run() -> set[str]:
        mcp_server_mod.initialize_mcp()
        mcp = mcp_server_mod.get_mcp()
        async with Client(mcp) as client:
            tools = await client.list_tools()
            return {t.name for t in tools}

    names = asyncio.run(_run())
    assert "list_relationships" in names
