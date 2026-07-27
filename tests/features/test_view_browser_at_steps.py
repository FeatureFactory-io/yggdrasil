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
    path = resolve_page_path("view-browse")
    at_context.response = at_context.test.client.get(path)
    view_browser_steps.step_view_browser_table_mode(at_context)
