"""Tests for View Browser pytest fixtures and seed helpers."""

from __future__ import annotations

import pytest

from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.fixtures.view_browser import (
    VIEW_BROWSER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
    _seed_view_browser,
)
from yggdrasil.graph.models import Element, Relationship, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope

EXPLORER_SLUGS = (
    "yggdrasil",
    "browser-htmx",
    "ai-agents",
    "backend-web-celery",
    "mcp-facade",
    "ratatosk-cli",
    "worker",
    "auth",
    "graph",
    "changeset",
    "munin",
    "ratatosk",
    "mcp",
    "api",
    "web",
    "llm",
    "postgre-sql",
    "redis",
    "ollama",
)


def test_explorer_elements_has_nineteen_rows_with_explicit_slugs() -> None:
    """VIEW_BROWSER_EXPLORER_ELEMENTS mirrors mockup self-model with slug column."""
    assert len(VIEW_BROWSER_EXPLORER_ELEMENTS) == 19
    slugs = [row[6] for row in VIEW_BROWSER_EXPLORER_ELEMENTS]
    assert slugs == list(EXPLORER_SLUGS)


def test_explorer_relationships_has_eleven_rows() -> None:
    """Explorer fixture seeds eleven relationships for graph coverage."""
    assert len(VIEW_BROWSER_EXPLORER_RELATIONSHIPS) == 11


@pytest.mark.django_db
def test_seed_view_browser_creates_elements_and_relationships(view_browser_user) -> None:
    """_seed_view_browser creates elements and relationships via ChangeSet pipeline."""
    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Seed Test", slug="seed-test", metamodel=mm)
    _seed_view_browser(
        model,
        VIEW_BROWSER_ELEMENTS,
        (),
        run_id="run-seed-test",
    )
    assert Element.objects.filter(model=model).count() == len(VIEW_BROWSER_ELEMENTS)
    set_current_user_id(None)


@pytest.mark.django_db
def test_view_browser_explorer_model_yields_nineteen_elements(view_browser_explorer_model) -> None:
    """Explorer fixture yields 19 elements across Context, Application, Technology."""
    count = Element.objects.filter(model=view_browser_explorer_model).count()
    assert count == 19
    packages = {
        el.package.slug
        for el in Element.objects.filter(model=view_browser_explorer_model).select_related(
            "package"
        )
    }
    assert packages == {"context", "application", "technology"}


@pytest.mark.django_db
def test_view_browser_explorer_model_has_eleven_relationships(view_browser_explorer_model) -> None:
    """Explorer fixture seeds eleven relationships."""
    count = Relationship.objects.filter(model=view_browser_explorer_model).count()
    assert count == len(VIEW_BROWSER_EXPLORER_RELATIONSHIPS)
