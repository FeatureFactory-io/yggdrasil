"""Unit tests for View Browser AT step definitions."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from django.urls import reverse

_FEATURES_ROOT = Path(__file__).resolve().parents[2] / "docs" / "features"
if str(_FEATURES_ROOT) not in sys.path:
    sys.path.insert(0, str(_FEATURES_ROOT))

from steps import navigation_steps, view_browser_steps  # noqa: E402
from support.pages import resolve_page_path  # noqa: E402
from tests.fixtures.factories import UserFactory  # noqa: E402

from yggdrasil.graph.models import Element  # noqa: E402


class _FakeContext:
    """Minimal behave context stub for step unit tests."""

    def __init__(self) -> None:
        self.test = None
        self.current_user = None
        self.response = None


@pytest.fixture
def at_context(db):
    """Authenticated AT context with Django test client."""
    from django.test import Client

    ctx = _FakeContext()
    user = UserFactory(is_architect=True)
    ctx.current_user = user
    client = Client()
    client.force_login(user)
    ctx.test = type("T", (), {"client": client})()
    return ctx


def test_resolve_page_path_view_browse() -> None:
    """PAGE_REGISTRY maps view-browse to /views/."""
    assert resolve_page_path("view-browse") == reverse("web:view_browse")


@pytest.mark.django_db
def test_given_view_browser_fixture_seeds_six_elements(at_context) -> None:
    """Given view browser fixture creates six elements."""
    view_browser_steps.step_model_loaded_view_browser_fixture(at_context, "yggdrasil")
    assert Element.objects.filter(model__slug="yggdrasil").count() == 6


@pytest.mark.django_db
def test_given_explorer_fixture_seeds_nineteen_elements(at_context) -> None:
    """Given explorer fixture creates nineteen elements."""
    view_browser_steps.step_model_loaded_explorer_fixture(at_context, "yggdrasil")
    assert Element.objects.filter(model__slug="yggdrasil").count() == 19


@pytest.mark.django_db
def test_navigation_with_query_string(at_context) -> None:
    """Query navigation step hits GET /views/?package=technology."""
    navigation_steps.step_user_is_on_page_with_query(
        at_context, "view-browse", "package=technology"
    )
    assert at_context.response.status_code == 200


@pytest.mark.django_db
def test_inspector_element_partial_step(at_context) -> None:
    """When I GET inspector element partial resolves slug to pk."""
    view_browser_steps.step_model_loaded_explorer_fixture(at_context, "yggdrasil")
    view_browser_steps.step_get_inspector_element_partial(at_context, "auth")
    body = at_context.response.content.decode()
    assert at_context.response.status_code == 200
    assert "Properties" in body
    assert "nav-view-browser" not in body


@pytest.mark.django_db
def test_table_mode_step(at_context) -> None:
    """Table mode step detects yrg-mode-table on browse page."""
    from tests.fixtures.factories.model_factories import YggdrasilModelFactory
    from tests.fixtures.view_browser import (
        _PAYMENT_RELATIONSHIPS,
        VIEW_BROWSER_ELEMENTS,
        _seed_view_browser,
    )

    from yggdrasil.graph.models import ensure_c4_metamodel

    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    _seed_view_browser(
        model, VIEW_BROWSER_ELEMENTS, _PAYMENT_RELATIONSHIPS, run_id="run-at-table-mode"
    )
    path = reverse("web:view_browse_model", kwargs={"model_slug": "yggdrasil"})
    at_context.response = at_context.test.client.get(path, {"view": "table"})
    view_browser_steps.step_view_browser_table_mode(at_context)


@pytest.mark.django_db
def test_select_model_in_switcher(at_context) -> None:
    """Scenario 51 AT: switcher navigates to payments model without munin."""
    from django.contrib.auth.models import Group

    user = UserFactory(groups="architect")
    at_context.current_user = user
    at_context.test.client.force_login(user)
    architect_group, _ = Group.objects.get_or_create(name="architect")
    user.groups.add(architect_group)
    view_browser_steps.step_two_models_readable(at_context, "yggdrasil", "payments")
    view_browser_steps.step_priya_on_view_browser_for_model(at_context, "yggdrasil")
    view_browser_steps.step_select_model_in_switcher(at_context, "payments")
    view_browser_steps.step_she_is_on_path(at_context, "/models/payments/views/")
    view_browser_steps.step_she_does_not_see_in_navigator(at_context, "munin")
