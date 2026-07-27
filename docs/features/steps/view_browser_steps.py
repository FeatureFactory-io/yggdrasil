"""
View Browser AT steps — fixtures, persona navigation, interaction stubs.

Step patterns (Domain: View Browser):
  - Given the model "{slug}" is loaded with the view browser fixture
  - Given the model "{slug}" is loaded with the view browser explorer fixture
  - Given Priya is on the View Browser
  - Given Priya is on the View Browser in graph mode
  - Given Priya is on the View Browser with the navigator expanded
  - When she toggles the "{slug}" package in the navigator  (W8 — NotImplementedError)
  - When she searches the navigator for "{query}"  (W8)
  - When she selects "{name}" in the navigator  (W8)
  - Then the inspector shows element "{name}"  (W9)
  - Then the graph view is active  (W10)
  - Then the table view is active  (AT)
  - Then the view browser is in table mode  (AT)
  - Then the view browser is in graph mode  (AT)
  - Then the graph-only panels are hidden  (AT)
  - Then the graph canvas controls are visible  (AT)
  - When I GET the view browser inspector element partial for "{slug}"  (AT)
  - When I GET the view browser inspector relationship partial from "{source}" to "{target}"  (AT)
"""

from __future__ import annotations

import logging
import re

from behave import given, then, when
from django.urls import reverse
from steps.common_steps import get_client
from support.visibility import (
    browser_ssr_mode,
    graph_only_panel_testids,
    is_element_ssr_hidden,
    opening_tag_for_testid,
)
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.fixtures.view_browser import (
    _PAYMENT_RELATIONSHIPS,
    VIEW_BROWSER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
    _seed_view_browser,
)

from yggdrasil.graph.models import Element, Relationship, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope

logger = logging.getLogger(__name__)


def _load_fixture(context, model_slug: str, element_specs, relationship_specs, run_id: str) -> None:
    """Seed model via ChangeSet and store slug on context."""
    user = getattr(context, "current_user", None)
    if user is None:
        user = UserFactory(is_architect=True)
        context.current_user = user
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name=model_slug.title(), slug=model_slug, metamodel=mm)
    _seed_view_browser(model, element_specs, relationship_specs, run_id=run_id)
    context.view_browser_model_slug = model_slug
    logger.info(
        "Loaded view browser fixture model_slug=%s elements=%s", model_slug, len(element_specs)
    )


@given('the model "{slug}" is loaded with the view browser fixture')
def step_model_loaded_view_browser_fixture(context, slug: str) -> None:
    """Seed six-element payment fixture on the given model slug."""
    _load_fixture(
        context, slug, VIEW_BROWSER_ELEMENTS, _PAYMENT_RELATIONSHIPS, "run-at-view-browser"
    )


@given('the model "{slug}" is loaded with the view browser explorer fixture')
def step_model_loaded_explorer_fixture(context, slug: str) -> None:
    """Seed nineteen-element Yggdrasil self-model explorer fixture."""
    _load_fixture(
        context,
        slug,
        VIEW_BROWSER_EXPLORER_ELEMENTS,
        VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
        "run-at-view-browser-explorer",
    )
    count = Element.objects.filter(model__slug=slug).count()
    assert count == 19, f"Expected 19 explorer elements, got {count}"


@given("Priya is on the View Browser")
def step_priya_on_view_browser(context) -> None:
    """GET production View Browser (not mockup)."""
    path = reverse("web:view_browse")
    context.response = get_client(context).get(path)
    logger.info("Priya on View Browser GET %s -> %s", path, context.response.status_code)


@given("Priya is on the View Browser in graph mode")
def step_priya_on_view_browser_graph_mode(context) -> None:
    """GET View Browser with ``?view=graph`` (three-panel explorer)."""
    path = reverse("web:view_browse") + "?view=graph"
    context.response = get_client(context).get(path)
    logger.info("Priya on View Browser graph mode GET %s -> %s", path, context.response.status_code)


@given("Priya is on the View Browser with the navigator expanded")
def step_priya_on_view_browser_nav_expanded(context) -> None:
    """Open View Browser — navigator SSR expanded by default for Application."""
    step_priya_on_view_browser(context)


@when('she toggles the "{slug}" package in the navigator')
def step_toggle_package_in_navigator(context, slug: str) -> None:
    """Navigator package toggle — E2E in tests/e2e/steps/view_browser_steps.py (W8)."""
    raise NotImplementedError(f"Navigator package toggle for {slug!r} — implement in W8")


@when('she searches the navigator for "{query}"')
def step_search_navigator(context, query: str) -> None:
    """Navigator search — implement in W8."""
    raise NotImplementedError(f"Navigator search for {query!r} — implement in W8")


@when('she selects "{name}" in the navigator')
def step_select_in_navigator(context, name: str) -> None:
    """Navigator selection sync — implement in W8/W10."""
    raise NotImplementedError(f"Navigator select {name!r} — implement in W8")


@then('the inspector shows element "{name}"')
def step_inspector_shows_element(context, name: str) -> None:
    """Inspector embed content — implement in W9."""
    raise NotImplementedError(f"Inspector element {name!r} — implement in W9")


@when('I GET the view browser inspector element partial for "{slug}"')
def step_get_inspector_element_partial(context, slug: str) -> None:
    """GET ``/views/inspector/element/<pk>/`` for an element slug on the loaded model."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    element = Element.objects.get(model__slug=model_slug, slug=slug)
    path = reverse("web:view_browse_inspector_element", args=[element.pk])
    context.response = get_client(context).get(path)
    logger.info(
        "GET inspector element partial slug=%s pk=%s -> %s",
        slug,
        element.pk,
        context.response.status_code,
    )


@when('I GET the view browser inspector relationship partial from "{source}" to "{target}"')
def step_get_inspector_relationship_partial(context, source: str, target: str) -> None:
    """GET relationship inspector partial resolved by source/target element slugs."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    source_el = Element.objects.get(model__slug=model_slug, slug=source)
    target_el = Element.objects.get(model__slug=model_slug, slug=target)
    relationship = Relationship.objects.get(
        model__slug=model_slug,
        source=source_el,
        target=target_el,
    )
    path = reverse("web:view_browse_inspector_relationship", args=[relationship.pk])
    context.response = get_client(context).get(path)
    logger.info(
        "GET inspector relationship partial %s->%s pk=%s -> %s",
        source,
        target,
        relationship.pk,
        context.response.status_code,
    )


@then("the view browser is in table mode")
def step_view_browser_table_mode(context) -> None:
    """Assert SSR table mode on ``#browserRoot``."""
    content = context.response.content.decode()
    mode = browser_ssr_mode(content)
    assert mode == "table", f"Expected table mode on browser root, got {mode!r}"
    logger.info("View browser is in table mode")


@then("the view browser is in graph mode")
def step_view_browser_graph_mode(context) -> None:
    """Assert SSR graph mode on ``#browserRoot``."""
    content = context.response.content.decode()
    mode = browser_ssr_mode(content)
    assert mode == "graph", f"Expected graph mode on browser root, got {mode!r}"
    logger.info("View browser is in graph mode")


@then("the graph-only panels are hidden")
def step_graph_only_panels_hidden(context) -> None:
    """Assert navigator, inspector, and panel toggles are SSR-hidden in table mode."""
    content = context.response.content.decode()
    hidden = [tid for tid in graph_only_panel_testids() if not is_element_ssr_hidden(content, tid)]
    assert not hidden, f"Expected graph-only panels hidden, but visible: {hidden}"
    logger.info("Graph-only panels are SSR-hidden")


@then("the graph canvas controls are visible")
def step_graph_canvas_controls_visible(context) -> None:
    """Assert replot, zoom, fit, and node-count controls are SSR-visible."""
    content = context.response.content.decode()
    required = (
        "browser-canvas-controls",
        "graph-replot-btn",
        "graph-zoom-in",
        "graph-zoom-out",
        "graph-zoom-fit",
        "graph-node-count",
    )
    missing = [tid for tid in required if opening_tag_for_testid(content, tid) is None]
    assert not missing, f"Missing canvas control testids: {missing}"
    visible = [tid for tid in required if not is_element_ssr_hidden(content, tid)]
    assert len(visible) == len(
        required
    ), f"Expected all canvas controls visible, hidden: {set(required) - set(visible)}"
    logger.info("Graph canvas controls are visible")


@then("the graph view is active")
def step_graph_view_active(context) -> None:
    """Assert graph mode SSR markers (table view hidden, graph view shown)."""
    content = context.response.content.decode()
    assert 'id="graphView"' in content, "Expected graphView container"
    assert not is_element_ssr_hidden(
        content, "graph-cy-container"
    ), "Graph canvas should be visible"
    table_tag_match = re.search(r'<div id="tableView"([^>]*)>', content)
    assert table_tag_match is not None, "Expected tableView container"
    assert "d-none" in table_tag_match.group(1), "Table view should be SSR-hidden in graph mode"
    logger.info("Graph view is active")


@then("the table view is active")
def step_table_view_active(context) -> None:
    """Assert table mode SSR markers (graph view hidden)."""
    content = context.response.content.decode()
    graph_match = re.search(r'<div id="graphView"([^>]*)>', content)
    assert graph_match is not None, "Expected graphView container"
    assert "d-none" in graph_match.group(1), "Graph view should be SSR-hidden in table mode"
    table_match = re.search(r'<div id="tableView"([^>]*)>', content)
    assert table_match is not None, "Expected tableView container"
    assert "d-none" not in table_match.group(1), "Table view should be visible in table mode"
    logger.info("Table view is active")


@then('the navigator row for "{name}" is highlighted')
def step_navigator_row_highlighted(context, name: str) -> None:
    """Cross-panel sync — implement in W10."""
    raise NotImplementedError(f"Navigator highlight for {name!r} — implement in W10")
