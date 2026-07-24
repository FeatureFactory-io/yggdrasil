"""Tests for graph browse_service (Act 2 View Browser foundation)."""

from __future__ import annotations

import pytest

from yggdrasil.graph import browse_service
from yggdrasil.mcp.tools.query import list_elements as mcp_list_elements


@pytest.mark.django_db
def test_list_elements_no_filter_returns_all(view_browser_model) -> None:
    """F0: unfiltered list returns all six mock-aligned elements."""
    result = browse_service.list_elements(model_slug="yggdrasil", limit=50)
    names = {item["name"] for item in result.items}
    assert result.total == 6
    assert "Payment API" in names
    assert "Mobile App" in names


@pytest.mark.django_db
def test_list_elements_filter_package(view_browser_model) -> None:
    """F0: technology package filter excludes Context elements."""
    result = browse_service.list_elements(model_slug="yggdrasil", package="technology")
    names = {item["name"] for item in result.items}
    assert "Payment API" in names
    assert "Mobile App" not in names


@pytest.mark.django_db
def test_list_elements_filter_stereotype(view_browser_model) -> None:
    """F0: container stereotype filter returns only containers."""
    result = browse_service.list_elements(model_slug="yggdrasil", stereotype="container")
    names = {item["name"] for item in result.items}
    assert names == {"Payment API", "Notification Service"}


@pytest.mark.django_db
def test_subgraph_includes_edges_among_nodes(view_browser_model) -> None:
    """F0: subgraph JSON includes nodes and edges for filtered set."""
    payload = browse_service.subgraph_for_elements(model_slug="yggdrasil", package="technology")
    assert len(payload["elements"]) >= 3
    assert len(payload["edges"]) >= 1


@pytest.mark.django_db
def test_list_elements_mcp_delegates_to_service(view_browser_model, view_browser_user) -> None:
    """F0: MCP list_elements returns same count via shared service."""
    from yggdrasil.mcp.server import set_current_user_id

    set_current_user_id(view_browser_user.pk)
    mcp_result = mcp_list_elements(model="yggdrasil", limit=50)
    assert mcp_result["total"] == 6
    assert any(item["name"] == "Payment API" for item in mcp_result["items"])
