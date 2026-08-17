"""Tests for graph browse_service (Act 2 View Browser foundation)."""

from __future__ import annotations

import logging

import pytest
from django.contrib.auth.models import Group
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_service
from yggdrasil.mcp.tools.query import list_elements as mcp_list_elements


@pytest.mark.django_db
def test_list_readable_models_all_when_owner_group_null() -> None:
    """W12: user sees Models with null owner_group."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Beta", slug="beta")
    slugs = {model.slug for model in browse_service.list_readable_models(user)}
    assert slugs == {"alpha", "beta"}


@pytest.mark.django_db
def test_list_readable_models_filters_by_owner_group() -> None:
    """W12: user only sees Models owned by their group."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Shared", slug="shared", owner_group=architect_group)
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    slugs = {model.slug for model in browse_service.list_readable_models(user)}
    assert slugs == {"shared"}


@pytest.mark.django_db
def test_list_readable_models_superuser_sees_all() -> None:
    """W12: admin bypass sees every Model."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    admin = UserFactory(is_admin=True)
    YggdrasilModelFactory(name="Locked", slug="locked", owner_group=architect_group)
    slugs = {model.slug for model in browse_service.list_readable_models(admin)}
    assert "locked" in slugs


@pytest.mark.django_db
def test_resolve_default_model_sole_visible() -> None:
    """W12: exactly one readable Model becomes the default."""
    user = UserFactory()
    YggdrasilModelFactory(name="Only", slug="only")
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) == "only"


@pytest.mark.django_db
def test_resolve_default_model_cookie_preference() -> None:
    """W12: valid cookie wins over name ordering."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Zulu", slug="zulu")
    assert browse_service.resolve_default_model_slug(user, cookie_value="zulu") == "zulu"


@pytest.mark.django_db
def test_resolve_default_model_first_by_name() -> None:
    """W12: fallback is first readable Model by name."""
    user = UserFactory()
    YggdrasilModelFactory(name="Beta", slug="beta")
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) == "alpha"


@pytest.mark.django_db
def test_resolve_default_model_no_readable_returns_none() -> None:
    """W12: zero readable Models yields None."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) is None


@pytest.mark.django_db
def test_user_can_read_model_rejects_private() -> None:
    """W12: unreadable slug raises PermissionError."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    with pytest.raises(PermissionError):
        browse_service.user_can_read_model(user, "private")


@pytest.mark.django_db
def test_resolve_default_model_log_story_happy(caplog) -> None:
    """W12: default resolver emits branch beats."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Beta", slug="beta")
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.resolve_default_model_slug(user, cookie_value="beta")
    assert_log_story(
        caplog,
        where="browse_service.resolve_default_model_slug",
        beats={
            "entry": ["user_pk="],
            "cookie": ["reason=cookie", "model_slug=beta"],
        },
    )


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
