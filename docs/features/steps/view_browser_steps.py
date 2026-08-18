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

import json
import logging
import re
from urllib.parse import urlencode

from behave import given, then, when
from django.contrib.auth.models import Group
from django.http import QueryDict
from django.urls import reverse
from django.utils.text import slugify
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

from yggdrasil.graph import browse_view_service
from yggdrasil.graph.models import (
    BrowseView,
    Element,
    Relationship,
    YggdrasilModel,
    ensure_c4_metamodel,
)
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
@when('Priya is on the View Browser for model "{slug}"')
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


def _current_user(context):
    user = getattr(context, "current_user", None)
    assert user is not None, "No current user — log in first"
    return user


def _model_for_slug(slug: str) -> YggdrasilModel:
    mm = ensure_c4_metamodel()
    model, _ = YggdrasilModel.objects.get_or_create(
        slug=slug,
        defaults={"name": slug.title(), "metamodel": mm},
    )
    return model


def _save_browse_view(
    context, *, name: str, model_slug: str, package: str = "", stereotype: str = "", depth: int = 1
):
    user = _current_user(context)
    model = _model_for_slug(model_slug)
    payload = {
        "filters": {
            "packages": [package] if package else [],
            "element_stereotypes": [stereotype] if stereotype else [],
            "relationship_stereotypes": [],
        },
        "levels": {"depth": depth},
        "presentation": "graph",
    }
    browse_view_service.save_view(user, model, name=name, payload=payload)
    logger.info("Saved BrowseView name=%s model=%s", name, model_slug)


@given('Priya has saved a View named "{name}" for model "{model_slug}"')
def step_priya_saved_view_for_model(context, name: str, model_slug: str) -> None:
    """Seed a BrowseView owned by the current architect user."""
    _save_browse_view(context, name=name, model_slug=model_slug)


@given('Priya has saved a View named "{name}" with package "{package}" and depth {depth:d}')
def step_priya_saved_view_package_depth(context, name: str, package: str, depth: int) -> None:
    """Seed BrowseView with package filter and depth."""
    _save_browse_view(
        context,
        name=name,
        model_slug=getattr(context, "view_browser_model_slug", "yggdrasil"),
        package=package,
        depth=depth,
    )


@given('Priya has saved a View named "{name}" with stereotype "{stereotype}" and depth {depth:d}')
def step_priya_saved_view_stereotype_depth(context, name: str, stereotype: str, depth: int) -> None:
    """Seed BrowseView with stereotype filter and depth."""
    _save_browse_view(
        context,
        name=name,
        model_slug=getattr(context, "view_browser_model_slug", "yggdrasil"),
        stereotype=stereotype,
        depth=depth,
    )


@given('a View named "{name}" exists for model "{model_slug}"')
def step_view_exists_for_model(context, name: str, model_slug: str) -> None:
    """Seed BrowseView on another model (same owner as current user)."""
    _save_browse_view(context, name=name, model_slug=model_slug)


@given('an architect has saved a View named "{name}" for model "{model_slug}"')
def step_architect_saved_view(context, name: str, model_slug: str) -> None:
    """Seed BrowseView as architect while viewer may be logged in later."""
    architect = UserFactory(is_architect=True)
    Group.objects.get_or_create(name="architect")
    architect.groups.add(Group.objects.get(name="architect"))
    model = _model_for_slug(model_slug)
    payload = {
        "filters": {"packages": [], "element_stereotypes": [], "relationship_stereotypes": []},
        "levels": {"depth": 1},
        "presentation": "graph",
    }
    browse_view_service.save_view(architect, model, name=name, payload=payload)
    logger.info("Architect saved shared View name=%s", name)


@given("Priya is on the View Browser in graph mode with depth {depth:d}")
def step_priya_on_browser_graph_depth(context, depth: int) -> None:
    """GET browse URL with graph mode and depth."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    context.response = get_client(context).get(path, {"mode": "graph", "depth": str(depth)})
    context.active_depth = depth
    context.last_url = path + "?" + urlencode({"mode": "graph", "depth": str(depth)})
    logger.info("Priya on graph mode depth=%s", depth)


@given('Priya has applied package filter "{package}"')
def step_priya_applied_package(context, package: str) -> None:
    """Record active package filter on context for save step."""
    context.active_package_filter = package


@when('Priya saves the current browse session as View "{name}"')
def step_priya_saves_current_view(context, name: str) -> None:
    """POST save endpoint with current filter state from context."""

    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    package = getattr(context, "active_package_filter", "")
    depth = str(getattr(context, "active_depth", 2))
    post_data = QueryDict(mutable=True)
    post_data.update({"name": name, "depth": depth, "mode": "graph"})
    if package:
        post_data.setlist("package", [package])
    query = _browse_query_params(context)
    for key, values in query.items():
        if key.startswith("field_") or key in {"stereotype", "edge_stereotype", "package"}:
            post_data.setlist(key, values)
    path = reverse("web:view_browse_save", kwargs={"model_slug": model_slug})
    context.response = get_client(context).post(path, post_data)
    context.last_url = context.response.headers.get("Location", path)
    logger.info("Saved view %s -> %s", name, context.response.status_code)


@when('Priya selects View "{name}" from the Views dropdown')
def step_priya_selects_view(context, name: str) -> None:
    """GET expanded load URL for named View."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    user = _current_user(context)
    model = _model_for_slug(model_slug)
    view = browse_view_service.get_view(user, model, slugify(name))
    expanded = browse_view_service.expand_to_query_params(view)
    expanded["browse_view"] = [view.slug]
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    context.response = get_client(context).get(path, expanded)
    context.last_url = path + "?" + urlencode(expanded, doseq=True)
    context.browse_query_params = expanded
    logger.info("Selected View %s", name)


@when('Priya deletes View "{name}"')
def step_priya_deletes_view(context, name: str) -> None:
    """POST delete for named View."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    user = _current_user(context)
    view = browse_view_service.get_view(user, _model_for_slug(model_slug), slugify(name))
    path = reverse(
        "web:view_browse_delete",
        kwargs={"model_slug": model_slug, "view_slug": view.slug},
    )
    context.response = get_client(context).post(path)
    context.response = get_client(context).get(
        reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    )
    logger.info("Deleted View %s", name)


@when("Priya clears all browse filters in the View Browser")
def step_priya_clears_filters(context) -> None:
    """GET unfiltered browse URL (simulates Clear)."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    context.response = get_client(context).get(path, {"mode": "graph"})
    context.last_url = path + "?mode=graph"
    logger.info("Cleared browse filters")


@when('the viewer loads View "{name}" from the Views dropdown')
def step_viewer_loads_view(context, name: str) -> None:
    """GET browse_view slug as viewer."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    slug = slugify(name)
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    context.response = get_client(context).get(path, {"browse_view": slug})
    logger.info("Viewer loaded View %s", name)


@then('a BrowseView "{slug}" exists for model "{model_slug}" owned by Priya')
def step_browseview_exists(context, slug: str, model_slug: str) -> None:
    """Assert ORM row exists for current user."""
    user = _current_user(context)
    view = browse_view_service.get_view(user, _model_for_slug(model_slug), slug)
    assert view.slug == slug
    logger.info("BrowseView %s exists", slug)


@then('the stored View payload includes package "{package}" and depth {depth:d}')
def step_stored_payload_package_depth(context, package: str, depth: int) -> None:
    """Assert last saved View payload fields."""
    user = _current_user(context)
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    view = BrowseView.objects.filter(model__slug=model_slug, owner=user).latest("created_at")
    assert view.payload["filters"]["packages"] == [package]
    assert view.payload["levels"]["depth"] == depth
    logger.info("Payload verified package=%s depth=%s", package, depth)


@then("the browser URL includes {fragment}")
def step_browser_url_includes(context, fragment: str) -> None:
    """Assert last navigation URL contains fragment (e.g. stereotype=component)."""
    url = getattr(context, "last_url", "")
    assert fragment in url, f"Expected {fragment!r} in URL {url!r}"
    logger.info("URL includes %s", fragment)


def _browse_query_params(context) -> dict[str, list[str]]:
    """Return mutable browse query params accumulated on context."""
    params = getattr(context, "browse_query_params", None)
    if params is None:
        params = {}
        context.browse_query_params = params
    return params


def _append_param(context, key: str, value: str) -> None:
    """Append one repeated query param value on context."""
    params = _browse_query_params(context)
    params.setdefault(key, []).append(value)


@given('Priya is on the View Browser with element stereotype "{stereotype}" selected')
def step_priya_on_browser_with_stereotype(context, stereotype: str) -> None:
    """GET browse URL with element stereotype filter."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    _append_param(context, "stereotype", stereotype)
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = _browse_query_params(context)
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)
    logger.info("Priya on browser stereotype=%s", stereotype)


@given(
    'Priya has applied filters with element stereotype "{stereotype}" and fields "{field_a}" and "{field_b}"'
)
def step_priya_applied_filters_two_fields(
    context, stereotype: str, field_a: str, field_b: str
) -> None:
    """Record filters + field_map and GET browse page."""
    field_paths = {
        "Name": "name",
        "Owner": "owner",
        "Health": "health",
        "Jira key": "properties.jira_key",
    }
    _append_param(context, "stereotype", stereotype)
    for label in (field_a, field_b):
        path = field_paths.get(label, label.lower().replace(" ", "_"))
        _append_param(context, f"field_{stereotype}", path)
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = {**_browse_query_params(context), "mode": ["graph"], "depth": ["2"]}
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)
    logger.info("Applied filters stereotype=%s fields=%s,%s", stereotype, field_a, field_b)


@given(
    'Priya has applied filters with element stereotype "{stereotype}" and field "{field_label}" visible'
)
def step_priya_applied_filters_one_field(context, stereotype: str, field_label: str) -> None:
    """Record single visible field and GET browse page."""
    field_paths = {
        "Owner": "owner",
        "Name": "name",
        "Health": "health",
        "Jira key": "properties.jira_key",
    }
    _append_param(context, "stereotype", stereotype)
    _append_param(context, f"field_{stereotype}", field_paths.get(field_label, field_label.lower()))
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = {**_browse_query_params(context), "mode": ["graph"], "depth": ["2"]}
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)


@given('Priya has checked visible fields "{f1}", "{f2}", and "{f3}"')
def step_priya_checked_three_fields(context, f1: str, f2: str, f3: str) -> None:
    """Record three field checkboxes for next apply step."""
    context.pending_field_labels = [f1, f2, f3]


@when("Priya applies browse filters")
def step_priya_applies_browse_filters(context) -> None:
    """GET browse URL with accumulated filter params (simulates Apply Filters)."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = dict(_browse_query_params(context))
    for label in getattr(context, "pending_field_labels", []):
        field_paths = {"Name": "name", "Owner": "owner", "Health": "health"}
        stereotype = query.get("stereotype", ["component"])[0]
        query.setdefault(f"field_{stereotype}", []).append(field_paths.get(label, label.lower()))
    query.setdefault("mode", ["graph"])
    query.setdefault("depth", ["2"])
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)
    context.browse_query_params = query
    logger.info("Priya applied browse filters")


@when('Priya selects element stereotype "{stereotype}"')
def step_priya_selects_element_stereotype(context, stereotype: str) -> None:
    """Select element stereotype in filter panel (pre-apply)."""
    _append_param(context, "stereotype", stereotype)


@when('Priya checks visible field "{field_label}" for stereotype "{stereotype}"')
def step_priya_checks_visible_field(context, field_label: str, stereotype: str) -> None:
    """Check one visible field path before apply."""
    field_paths = {"Jira key": "properties.jira_key", "Owner": "owner", "Name": "name"}
    _append_param(context, f"field_{stereotype}", field_paths.get(field_label, field_label.lower()))


@when("Priya toggles to table mode")
def step_priya_toggles_table_mode(context) -> None:
    """GET same filters with table presentation mode."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = dict(_browse_query_params(context))
    query["mode"] = ["table"]
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)


@then('graph node "{slug}" displays label containing "{text}"')
def step_graph_node_label_contains(context, slug: str, text: str) -> None:
    """Assert graph JSON label for element slug contains text fragment."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    element = Element.objects.get(model__slug=model_slug, slug=slug)
    graph_path = reverse("web:view_browse_graph_model", kwargs={"model_slug": model_slug})
    query = dict(_browse_query_params(context))
    query.setdefault("depth", ["2"])
    response = get_client(context).get(graph_path, query)
    assert response.status_code == 200, response.content
    payload = response.json()
    label = next(
        node["data"]["label"]
        for node in payload["elements"]
        if node["data"]["id"] == str(element.pk)
    )
    assert text in label, f"Expected {text!r} in label {label!r}"
    logger.info("Graph node %s label contains %s", slug, text)


@then('the table includes column "{column_label}"')
def step_table_includes_column(context, column_label: str) -> None:
    """Assert SSR table header includes column label."""
    body = context.response.content.decode()
    assert (
        f">{column_label}</th>" in body or f">{column_label}</th" in body
    ), f"Column {column_label!r} not found"


@then('the stored View payload includes field_map for stereotype "{stereotype}"')
def step_stored_payload_includes_field_map(context, stereotype: str) -> None:
    """Assert last saved View has field_map entry for stereotype."""
    user = _current_user(context)
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    view = BrowseView.objects.filter(model__slug=model_slug, owner=user).latest("created_at")
    field_map = view.payload.get("content", {}).get("field_map", {})
    assert field_map.get(stereotype), f"Missing field_map for {stereotype}"


@given('Priya has saved a View named "{name}" with field_map for "{stereotype}"')
def step_priya_saved_view_with_field_map(context, name: str, stereotype: str) -> None:
    """Seed BrowseView with field_map for one stereotype."""
    user = _current_user(context)
    model = _model_for_slug(getattr(context, "view_browser_model_slug", "yggdrasil"))
    payload = {
        "filters": {
            "packages": [],
            "element_stereotypes": [stereotype],
            "relationship_stereotypes": [],
        },
        "levels": {"depth": 2},
        "presentation": "graph",
        "content": {"field_map": {stereotype: ["name", "owner"]}},
    }
    browse_view_service.save_view(user, model, name=name, payload=payload)
    logger.info("Saved View %s with field_map for %s", name, stereotype)


@given(
    'a BrowseView "{name}" exists for model "{model_slug}" with presentation table and a saved viewport'
)
def step_browseview_table_with_viewport(context, name: str, model_slug: str) -> None:
    """Seed a table-mode View whose payload still carries a graph viewport."""
    user = _current_user(context)
    model = _model_for_slug(model_slug)
    payload = {
        "filters": {"packages": [], "element_stereotypes": [], "relationship_stereotypes": []},
        "levels": {"depth": 1},
        "presentation": "table",
        "viewport": {"zoom": 2.0, "pan": {"x": 120, "y": 80}},
    }
    browse_view_service.save_view(user, model, name=name, payload=payload)
    logger.info("Seeded table View %s with viewport for model %s", name, model_slug)


@then("the graph canvas controls are hidden")
def step_graph_canvas_controls_hidden(context) -> None:
    """Assert zoom/fit controls are SSR-hidden (table mode)."""
    content = context.response.content.decode()
    controls = opening_tag_for_testid(content, "browser-canvas-controls")
    assert controls is not None, "Expected browser-canvas-controls element"
    assert is_element_ssr_hidden(
        content, "browser-canvas-controls"
    ), "Graph canvas controls should be hidden in table mode"
    assert "loaded-viewport" not in content, "Table mode must not embed graph viewport JSON"
    logger.info("Graph canvas controls are hidden")


@given("Priya is on the View Browser with the filter panel open")
def step_priya_filter_panel_open(context) -> None:
    """GET browse page (filters panel markup is always in DOM)."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    context.response = get_client(context).get(path, {"mode": "graph"})
    context.last_url = path + "?mode=graph"
    logger.info("Priya on View Browser with filter panel available")


@when('Priya selects package "{package}" in the filter panel')
def step_priya_selects_package_in_filter_panel(context, package: str) -> None:
    """Select package in filter panel and refresh SSR (scoped stereotype catalog)."""
    _append_param(context, "package", package)
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    path = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    query = {**_browse_query_params(context), "mode": ["graph"]}
    context.response = get_client(context).get(path, query)
    context.last_url = path + "?" + urlencode(query, doseq=True)
    logger.info("Priya selected package=%s in filter panel", package)


def _stereotype_option_slugs(content: str) -> set[str]:
    """Parse element stereotype option values from filter-stereotype select."""
    match = re.search(
        r'data-testid="filter-stereotype"[^>]*>(.*?)</select>',
        content,
        re.DOTALL,
    )
    assert match is not None, "filter-stereotype select not found"
    return set(re.findall(r'<option value="([^"]+)"', match.group(1)))


@then('the element stereotype filter includes "{stereotype}"')
def step_stereotype_filter_includes(context, stereotype: str) -> None:
    """Assert stereotype appears in filter-stereotype options."""
    slugs = _stereotype_option_slugs(context.response.content.decode())
    assert stereotype in slugs, f"Expected {stereotype!r} in {slugs}"


@then('the element stereotype filter does not include "{stereotype}"')
def step_stereotype_filter_excludes(context, stereotype: str) -> None:
    """Assert stereotype is absent from filter-stereotype options."""
    slugs = _stereotype_option_slugs(context.response.content.decode())
    assert stereotype not in slugs, f"Expected {stereotype!r} absent from {slugs}"


@when('Priya saves the current browse session as View "{name}" including viewport')
def step_priya_saves_view_including_viewport(context, name: str) -> None:
    """POST save with viewport JSON from context (simulates include-viewport checkbox)."""
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    post_data = QueryDict(mutable=True)
    post_data.update({"name": name, "depth": "2", "mode": "graph"})
    viewport = getattr(context, "captured_viewport", {"zoom": 1.8, "pan": {"x": 50, "y": 30}})
    post_data["viewport"] = json.dumps(viewport)
    query = _browse_query_params(context)
    for key, values in query.items():
        if key.startswith("field_") or key in {"stereotype", "edge_stereotype", "package"}:
            post_data.setlist(key, values)
    path = reverse("web:view_browse_save", kwargs={"model_slug": model_slug})
    context.response = get_client(context).post(path, post_data)
    context.last_url = context.response.headers.get("Location", path)
    logger.info("Saved view %s with viewport", name)


@when('Priya reloads View "{name}"')
def step_priya_reloads_view(context, name: str) -> None:
    """GET saved View by slug (follow save redirect flow)."""
    step_priya_selects_view(context, name)


@then('graph node "{slug}" is centered in the canvas viewport')
def step_graph_node_centered_in_viewport(context, slug: str) -> None:
    """Assert saved View carries viewport focus and reload embeds it for graph mode."""
    user = _current_user(context)
    model_slug = getattr(context, "view_browser_model_slug", "yggdrasil")
    view = BrowseView.objects.filter(model__slug=model_slug, owner=user).latest("created_at")
    viewport = view.payload.get("viewport") or {}
    assert (
        viewport.get("center_element_id") == slug
    ), f"Expected viewport center_element_id={slug!r}, got {viewport!r}"
    body = context.response.content.decode()
    assert "loaded-viewport" in body, "Graph reload should embed viewport JSON script"
    assert slug in body, f"Expected {slug!r} in embedded viewport JSON"
    logger.info("Viewport for %s persisted and embedded on reload", slug)


@given('Priya has panned and zoomed the graph to focus element "{slug}"')
def step_priya_panned_zoomed_to_element(context, slug: str) -> None:
    """Record simulated viewport state for save-viewport scenario."""
    context.captured_viewport = {
        "zoom": 1.8,
        "pan": {"x": 40, "y": 20},
        "center_element_id": slug,
    }
    logger.info("Recorded viewport focus on element %s", slug)
