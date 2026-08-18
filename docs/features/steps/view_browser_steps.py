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
from django.contrib.auth.models import Group
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
        user = UserFactory(groups="architect")
        context.current_user = user
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model, _ = YggdrasilModelFactory._meta.model.objects.get_or_create(
        slug=model_slug,
        defaults={"name": model_slug.title(), "metamodel": mm},
    )
    if Element.objects.filter(model=model).exists():
        context.view_browser_model_slug = model_slug
        logger.info("View browser fixture already loaded model_slug=%s", model_slug)
        return
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


@given('the models "{model_a}" and "{model_b}" exist and the architect can read both')
def step_two_models_readable(context, model_a: str, model_b: str) -> None:
    """Seed two models with explorer/payment fixtures; architect group owns both."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    user = getattr(context, "current_user", None)
    if user is not None:
        user.groups.add(architect_group)
    mm = ensure_c4_metamodel()
    yggdrasil, _ = YggdrasilModelFactory._meta.model.objects.get_or_create(
        slug=model_a,
        defaults={"name": model_a.title(), "metamodel": mm, "owner_group": architect_group},
    )
    if yggdrasil.owner_group_id is None:
        yggdrasil.owner_group = architect_group
        yggdrasil.save(update_fields=["owner_group"])
    payments, _ = YggdrasilModelFactory._meta.model.objects.get_or_create(
        slug=model_b,
        defaults={"name": model_b.title(), "metamodel": mm, "owner_group": architect_group},
    )
    if not Element.objects.filter(model=yggdrasil).exists():
        _seed_view_browser(
            yggdrasil,
            VIEW_BROWSER_EXPLORER_ELEMENTS,
            VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
            run_id="run-at-two-model-yggdrasil",
        )
    if not Element.objects.filter(model=payments).exists():
        _seed_view_browser(
            payments,
            VIEW_BROWSER_ELEMENTS,
            _PAYMENT_RELATIONSHIPS,
            run_id="run-at-two-model-payments",
        )
    context.view_browser_model_slug = model_a
    logger.info("Seeded readable models %s and %s", model_a, model_b)


@given("the architect can read no models")
def step_architect_can_read_no_models(context) -> None:
    """Ensure no model is readable by the signed-in architect."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    from yggdrasil.graph.models import YggdrasilModel

    YggdrasilModel.objects.update(owner_group=other_group)
    if not YggdrasilModel.objects.filter(slug="private").exists():
        mm = ensure_c4_metamodel()
        YggdrasilModelFactory(name="Private", slug="private", metamodel=mm, owner_group=other_group)
    logger.info("Architect cannot read any models")


@given('Priya is on the View Browser for model "{slug}"')
def step_priya_on_view_browser_for_model(context, slug: str) -> None:
    """GET canonical browse URL for a specific model."""
    path = reverse("web:view_browse_model", kwargs={"model_slug": slug})
    context.response = get_client(context).get(path)
    context.current_path = path
    context.view_browser_model_slug = slug
    logger.info(
        "Priya on View Browser model=%s GET %s -> %s", slug, path, context.response.status_code
    )


@given("Priya is on the View Browser")
def step_priya_on_view_browser(context) -> None:
    """GET production View Browser (follows alias redirect)."""
    path = reverse("web:view_browse")
    context.response = get_client(context).get(path, follow=True)
    logger.info("Priya on View Browser GET %s -> %s", path, context.response.status_code)


@given("Priya is on the View Browser in graph mode")
def step_priya_on_view_browser_graph_mode(context) -> None:
    """GET View Browser with ``?mode=graph`` (follows alias redirect)."""
    path = reverse("web:view_browse") + "?mode=graph"
    context.response = get_client(context).get(path, follow=True)
    logger.info("Priya on View Browser graph mode GET %s -> %s", path, context.response.status_code)


@given("Priya is on the View Browser with the navigator expanded")
def step_priya_on_view_browser_nav_expanded(context) -> None:
    """Open View Browser — navigator SSR expanded by default for Application."""
    step_priya_on_view_browser(context)


@when('she selects model "{slug}" in the model switcher')
def step_select_model_in_switcher(context, slug: str) -> None:
    """Navigate to another Model via the switcher dropdown link (AT)."""
    path = reverse("web:view_browse_model", kwargs={"model_slug": slug})
    context.response = get_client(context).get(path)
    context.current_path = path
    context.view_browser_model_slug = slug
    logger.info(
        "Selected model %s in switcher GET %s -> %s",
        slug,
        path,
        context.response.status_code,
    )


@then('she is on "{path}"')
def step_she_is_on_path(context, path: str) -> None:
    """Assert the last navigation landed on ``path`` with HTTP 200."""
    assert (
        context.response.status_code == 200
    ), f"Expected 200 on {path!r}, got {context.response.status_code}"
    assert (
        getattr(context, "current_path", None) == path
    ), f"Expected current_path={path!r}, got {getattr(context, 'current_path', None)!r}"
    logger.info("Priya is on %s", path)


def _navigator_panel_html(content: str) -> str:
    """Extract navigator panel HTML for scoped text assertions."""
    match = re.search(
        r'<aside[^>]*data-testid="browser-nav-panel"[\s\S]*?</aside>',
        content,
    )
    return match.group(0) if match else content


@then('she sees "{text}" in the navigator')
def step_she_sees_in_navigator(context, text: str) -> None:
    """Assert ``text`` appears inside the navigator panel."""
    content = context.response.content.decode()
    navigator = _navigator_panel_html(content)
    assert text in navigator, f"Expected {text!r} in navigator panel"
    logger.info('Navigator shows "%s"', text)


@then('she does not see "{text}" in the navigator')
def step_she_does_not_see_in_navigator(context, text: str) -> None:
    """Assert ``text`` is absent from the navigator panel."""
    content = context.response.content.decode()
    navigator = _navigator_panel_html(content)
    assert text not in navigator, f"Expected {text!r} absent from navigator panel"
    logger.info('Navigator does not show "%s"', text)


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
    path = reverse(
        "web:view_browse_inspector_element_model",
        kwargs={"model_slug": model_slug, "pk": element.pk},
    )
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
    path = reverse(
        "web:view_browse_inspector_relationship_model",
        kwargs={"model_slug": model_slug, "pk": relationship.pk},
    )
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
