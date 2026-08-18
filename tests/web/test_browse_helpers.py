"""Unit tests for browse_helpers (W7 + W13)."""

from __future__ import annotations

import logging

import pytest
from django.test import RequestFactory
from tests.fixtures.factories import UserFactory
from tests.support.log_story import assert_log_story

from yggdrasil.web.browse_helpers import (
    DEFAULT_VIEW_MODE,
    build_package_tree,
    build_traversal_tree,
    build_view_browse_context,
    parse_view_browse_params,
)


def test_build_package_tree_groups_and_orders_packages() -> None:
    """Package tree orders Context → Application → Technology."""
    elements = [
        {"name": "Redis", "package": "Technology", "package_slug": "technology", "slug": "redis"},
        {"name": "auth", "package": "Application", "package_slug": "application", "slug": "auth"},
        {"name": "Yggdrasil", "package": "Context", "package_slug": "context", "slug": "yggdrasil"},
    ]
    tree = build_package_tree(elements)
    assert [node["slug"] for node in tree] == ["context", "application", "technology"]
    assert tree[1]["elements"][0]["name"] == "auth"


def test_parse_depth_defaults_to_1() -> None:
    """W13: omitted depth query param defaults to 1."""
    request = RequestFactory().get("/models/yggdrasil/views/")
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.depth == 1


def test_parse_view_defaults_to_graph() -> None:
    """Omitted mode/view query param defaults to graph presentation."""
    request = RequestFactory().get("/models/yggdrasil/views/")
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == DEFAULT_VIEW_MODE
    assert params.view_mode == "graph"


def test_parse_mode_query_param_table() -> None:
    """W14-0: ``?mode=table`` selects table presentation."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"mode": "table"})
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_parse_mode_prefers_mode_over_legacy_view() -> None:
    """W14-0: ``?mode=`` wins when both ``mode`` and legacy ``view`` are present."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        {"mode": "table", "view": "graph"},
    )
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_parse_legacy_view_query_param_fallback() -> None:
    """W14-0: legacy ``?view=`` still works as alias for ``?mode=``."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"view": "table"})
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_build_traversal_tree_nests_children() -> None:
    """W13: parent/child nesting from BFS parent map."""
    rows = [
        {"id": 1, "name": "munin", "slug": "munin", "stereotype": "Component", "health": "green"},
        {"id": 2, "name": "llm", "slug": "llm", "stereotype": "Component", "health": "green"},
    ]
    parent_map = {1: None, 2: 1}
    tree = build_traversal_tree(rows, parent_map, frozenset({1}))
    assert len(tree) == 1
    assert tree[0]["slug"] == "munin"
    assert tree[0]["children"][0]["slug"] == "llm"


def test_build_traversal_tree_log_story_happy(caplog) -> None:
    """W13: traversal tree build logs tree_root_count."""
    rows = [
        {"id": 1, "name": "auth", "slug": "auth", "stereotype": "Component", "health": "green"},
    ]
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        build_traversal_tree(rows, {1: None}, frozenset({1}))
    assert_log_story(
        caplog,
        where="build_traversal_tree",
        beats={
            "exit": ["tree_root_count=", "element_count="],
        },
    )


@pytest.mark.django_db
def test_build_view_browse_context_includes_slugs_and_traversal(view_browser_model) -> None:
    """build_view_browse_context rows include slug fields and traversal tree."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/", {"depth": "3"})
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    context = build_view_browse_context(request, params)
    assert context["element_count"] == 6
    assert context["traversal_roots"]
    assert context["current_depth"] == 3
    assert context["model_name"] == "Yggdrasil"
    row = context["elements"][0]
    for key in ("slug", "stereotype_slug", "package_slug"):
        assert row.get(key)


@pytest.mark.django_db
def test_build_view_browse_context_returns_traversal_fields(view_browser_model) -> None:
    """Context includes traversal_roots and model_name from resolve_model."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/")
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    context = build_view_browse_context(request, params)
    assert context["traversal_roots"]
    assert context["model_name"] == "Yggdrasil"
    assert context["element_count"] == 4
