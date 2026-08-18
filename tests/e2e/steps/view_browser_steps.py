"""
View Browser E2E steps (Playwright).

Steps:
  - Given Priya is logged in for View Browser E2E
  - Given Priya is on the View Browser
  - Given Priya is on the View Browser for model "{slug}"
  - Given the E2E models "yggdrasil" and "payments" are seeded
  - When she selects model "{slug}" in the model switcher
  - Then she is on "{path}"
  - Then she does not see "{text}" in the navigator
"""

from __future__ import annotations

import logging

from behave import given, then, when
from django.contrib.auth.models import Group
from django.urls import reverse
from tests.fixtures.factories import UserFactory
from tests.fixtures.view_browser import (
    _PAYMENT_RELATIONSHIPS,
    VIEW_BROWSER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
    _seed_view_browser,
)

from yggdrasil.graph.models import Element, YggdrasilModel, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope

logger = logging.getLogger(__name__)


def _live_server_base(context) -> str:
    """Return live server root URL from behave-django."""
    return context.test.live_server_url.rstrip("/")


def _force_login_playwright(context, user) -> None:
    """Inject Django session cookie so Playwright requests are authenticated."""
    from django.test import Client

    client = Client()
    client.force_login(user)
    client.get("/")
    session_key = client.cookies["sessionid"].value
    base = _live_server_base(context)
    context.page.goto(base + "/")
    context.page.context.add_cookies(
        [
            {
                "name": "sessionid",
                "value": session_key,
                "url": base + "/",
            }
        ]
    )
    context.current_user = user
    logger.info("E2E session login user_pk=%s session_key=%s", user.pk, session_key[:8])


def _seed_two_models(context) -> None:
    """Seed yggdrasil explorer + payments fixtures for switcher E2E."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    user = getattr(context, "current_user", None)
    if user is not None:
        user.groups.add(architect_group)
    set_current_user_id(user.pk if user else None)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    yggdrasil, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": mm, "owner_group": architect_group},
    )
    payments, _ = YggdrasilModel.objects.get_or_create(
        slug="payments",
        defaults={"name": "Payments", "metamodel": mm, "owner_group": architect_group},
    )
    if not Element.objects.filter(model=yggdrasil).exists():
        _seed_view_browser(
            yggdrasil,
            VIEW_BROWSER_EXPLORER_ELEMENTS,
            VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
            run_id="run-e2e-two-model-yggdrasil",
        )
    if not Element.objects.filter(model=payments).exists():
        _seed_view_browser(
            payments,
            VIEW_BROWSER_ELEMENTS,
            _PAYMENT_RELATIONSHIPS,
            run_id="run-e2e-two-model-payments",
        )


@given("Priya is logged in for View Browser E2E")
def step_priya_logged_in_e2e(context) -> None:
    """Create architect user and authenticate Playwright via session cookie."""
    user = UserFactory(groups="architect")
    user.set_password("test-pass-only-1234")
    user.save()
    _force_login_playwright(context, user)


@given('Priya is on the View Browser for model "{slug}"')
def step_priya_on_view_browser_model_e2e(context, slug: str) -> None:
    """Open canonical model-scoped View Browser in Playwright."""
    if not getattr(context, "current_user", None):
        step_priya_logged_in_e2e(context)
    path = reverse("web:view_browse_model", kwargs={"model_slug": slug})
    url = _live_server_base(context) + path + "?mode=graph"
    context.page.goto(url, wait_until="networkidle")
    context.current_path = path
    logger.info("E2E opened View Browser model=%s at %s", slug, url)


@given("Priya is on the View Browser")
def step_priya_on_view_browser_e2e(context) -> None:
    """Open View Browser alias (follows redirect to default model)."""
    if not getattr(context, "current_user", None):
        step_priya_logged_in_e2e(context)
    path = reverse("web:view_browse")
    url = _live_server_base(context) + path
    context.page.goto(url, wait_until="networkidle")
    context.current_path = context.page.url.replace(_live_server_base(context), "")
    logger.info("E2E opened View Browser at %s", context.page.url)


@given("Priya is on the View Browser with the navigator expanded")
def step_priya_view_browser_nav_expanded_e2e(context) -> None:
    """Open View Browser — navigator SSR expanded for Application package."""
    step_priya_on_view_browser_e2e(context)


@given('the E2E models "yggdrasil" and "payments" are seeded')
def step_e2e_two_models_seeded(context) -> None:
    """Seed two-model fixture after login for switcher E2E."""
    if not getattr(context, "current_user", None):
        step_priya_logged_in_e2e(context)
    _seed_two_models(context)


@when('she selects model "{slug}" in the model switcher')
def step_select_model_in_switcher_e2e(context, slug: str) -> None:
    """Click model switcher dropdown option in Playwright."""
    switcher = context.page.get_by_test_id("browser-model-switcher")
    switcher.wait_for(state="visible", timeout=10_000)
    switcher.click()
    option = context.page.get_by_test_id(f"browser-model-option-{slug}")
    option.wait_for(state="visible", timeout=5_000)
    option.click()
    expected_path = reverse("web:view_browse_model", kwargs={"model_slug": slug})
    context.page.wait_for_url(f"**{expected_path}**")
    context.current_path = expected_path
    logger.info("E2E selected model %s -> %s", slug, context.page.url)


@then('she is on "{path}"')
def step_she_is_on_path_e2e(context, path: str) -> None:
    """Assert Playwright browser URL ends with ``path``."""
    current = context.page.url.replace(_live_server_base(context), "")
    assert (
        current.startswith(path) or current == path
    ), f"Expected URL path {path!r}, got {current!r} (full: {context.page.url})"
    logger.info("E2E Priya is on %s", path)


@then('she does not see "{text}" in the navigator')
def step_she_does_not_see_in_navigator_e2e(context, text: str) -> None:
    """Assert text is absent from the navigator panel in Playwright."""
    navigator = context.page.get_by_test_id("browser-nav-panel")
    assert text not in navigator.inner_text(), f"Expected {text!r} absent from navigator"
    logger.info('E2E navigator does not show "%s"', text)


@given("the view browser explorer fixture is seeded for E2E")
def step_seed_explorer_fixture_e2e(context) -> None:
    """Seed yggdrasil explorer graph for depth-slider E2E."""
    if not getattr(context, "current_user", None):
        step_priya_logged_in_e2e(context)
    architect_group, _ = Group.objects.get_or_create(name="architect")
    context.current_user.groups.add(architect_group)
    set_current_user_id(context.current_user.pk)
    mm = ensure_c4_metamodel()
    yggdrasil, _ = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": mm, "owner_group": architect_group},
    )
    if not Element.objects.filter(model=yggdrasil).exists():
        _seed_view_browser(
            yggdrasil,
            VIEW_BROWSER_EXPLORER_ELEMENTS,
            VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
            run_id="run-e2e-explorer-depth",
        )
    logger.info("E2E explorer fixture seeded for yggdrasil")


@when('she sets the view browser depth slider to "{value}"')
def step_set_depth_slider_e2e(context, value: str) -> None:
    """Change Levels slider and fire change event (in-place graph update)."""
    slider = context.page.get_by_test_id("browser-depth-slider")
    slider.wait_for(state="visible", timeout=10_000)
    slider.fill(value)
    slider.dispatch_event("change")
    context.page.wait_for_timeout(500)
    logger.info("E2E depth slider set to %s url=%s", value, context.page.url)


@when('she applies package filter "{package}" on the view browser')
def step_apply_package_filter_e2e(context, package: str) -> None:
    """Select package filter and apply via in-page navigation."""
    context.page.get_by_test_id("filters-toggle").click()
    context.page.get_by_test_id("filter-package").select_option(package)
    context.page.get_by_test_id("apply-filters-btn").click()
    context.page.wait_for_load_state("networkidle")
    logger.info("E2E applied package filter %s url=%s", package, context.page.url)


@when("she clears filters on the view browser")
def step_clear_filters_e2e(context) -> None:
    """Click toolbar Clear filters (in-place when JS intercepts)."""
    context.page.get_by_test_id("clear-filters-btn").click()
    context.page.wait_for_timeout(800)
    logger.info("E2E cleared filters url=%s", context.page.url)


@then("the view browser is in graph mode in the browser")
def step_graph_mode_in_browser_e2e(context) -> None:
    """Assert #browserRoot has yrg-mode-graph after client-side depth change."""
    root = context.page.locator("#browserRoot")
    classes = root.get_attribute("class") or ""
    assert "yrg-mode-graph" in classes, f"Expected graph mode classes, got {classes!r}"
    assert "yrg-mode-table" not in classes.split(), f"Expected not table mode, got {classes!r}"
    logger.info("E2E view browser in graph mode")


@then("the graph view is visible in the browser")
def step_graph_view_visible_e2e(context) -> None:
    """Assert #graphView is visible (not d-none)."""
    graph = context.page.locator("#graphView")
    graph.wait_for(state="attached", timeout=5_000)
    assert "d-none" not in (graph.get_attribute("class") or ""), "Graph view is hidden"
    logger.info("E2E graph view visible")
