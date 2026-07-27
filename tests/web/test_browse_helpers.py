"""Unit tests for browse_helpers (W7)."""

from __future__ import annotations

import pytest
from django.test import RequestFactory
from tests.fixtures.factories import UserFactory

from yggdrasil.web.browse_helpers import (
    build_package_tree,
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


@pytest.mark.django_db
def test_build_view_browse_context_includes_slugs_and_packages(view_browser_explorer_model) -> None:
    """build_view_browse_context rows include slug fields and package tree."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/views/")
    request.user = user
    params = parse_view_browse_params(request)
    context = build_view_browse_context(request, params)
    assert context["element_count"] == 19
    assert len(context["packages"]) == 3
    assert context["model_name"] == "Yggdrasil"
    row = context["elements"][0]
    for key in ("slug", "stereotype_slug", "package_slug"):
        assert row.get(key)


@pytest.mark.django_db
def test_build_view_browse_context_returns_packages(view_browser_explorer_model) -> None:
    """Context includes packages list and model_name from resolve_model."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/views/")
    request.user = user
    params = parse_view_browse_params(request)
    context = build_view_browse_context(request, params)
    assert context["packages"]
    assert context["model_name"] == "Yggdrasil"
    assert context["element_count"] == 19
