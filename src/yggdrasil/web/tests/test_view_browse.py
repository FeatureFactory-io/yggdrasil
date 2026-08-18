"""VIEW-BROWSE-1 web view tests."""

from __future__ import annotations

import json
import logging

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.fixtures.view_browser import (
    _PAYMENT_RELATIONSHIPS,
    VIEW_BROWSER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_ELEMENTS,
    VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
    _seed_view_browser,
)
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_service
from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope


def _browse_url(model_slug: str = "yggdrasil") -> str:
    """Canonical model-scoped browse URL."""
    return reverse("web:view_browse_model", kwargs={"model_slug": model_slug})


def _browse_graph_url(model_slug: str = "yggdrasil") -> str:
    """Canonical model-scoped graph JSON URL."""
    return reverse("web:view_browse_graph_model", kwargs={"model_slug": model_slug})


GRAPH_URL = _browse_url("yggdrasil") + "?mode=graph"


@pytest.fixture
def two_model_fixture(db, view_browser_user):
    """Yggdrasil explorer + Payments payment models readable by architect."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    view_browser_user.groups.add(architect_group)
    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    yggdrasil = YggdrasilModelFactory(
        name="Yggdrasil",
        slug="yggdrasil",
        metamodel=mm,
        owner_group=architect_group,
    )
    payments = YggdrasilModelFactory(
        name="Payments",
        slug="payments",
        metamodel=mm,
        owner_group=architect_group,
    )
    _seed_view_browser(
        yggdrasil,
        VIEW_BROWSER_EXPLORER_ELEMENTS,
        VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
        run_id="run-two-model-yggdrasil",
    )
    _seed_view_browser(
        payments,
        VIEW_BROWSER_ELEMENTS,
        _PAYMENT_RELATIONSHIPS,
        run_id="run-two-model-payments",
    )
    yield {"yggdrasil": yggdrasil, "payments": payments}
    set_current_user_id(None)
    set_token_scope("read-write")


@pytest.mark.django_db
def test_view_browser_shell_testids(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-01: shell exposes filter panel and table/graph toggles."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="view-browse-page"' in body
    assert 'data-testid="filters-toggle"' in body
    assert 'data-testid="filter-package"' in body
    assert 'data-testid="toggle-table"' in body
    assert 'data-testid="toggle-graph"' in body
    assert 'data-testid="results-container"' in body


@pytest.mark.django_db
def test_view_browser_subtitle_hides_internal_screen_id(
    client, view_browser_user, view_browser_model
):
    """Regression #98: page subtitle must not expose internal Screen ID."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="view-browser-subtitle"' in body
    start = body.index('data-testid="view-browser-subtitle"')
    end = body.index("</p>", start)
    subtitle = body[start:end]
    assert "VIEW-BROWSE-1" not in subtitle
    assert "Yggdrasil" in subtitle
    assert "elements visible" in subtitle


@pytest.mark.django_db
def test_default_view_shows_elements(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-02: default depth=1 lists graph source elements."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert response.status_code == 200
    for name in (
        "Mobile App",
        "Notification Service",
        "Order Domain",
        "Fulfillment Worker",
    ):
        assert name in body
    assert "Payment API" not in body


@pytest.mark.django_db
def test_table_columns_present(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-03: table shows stereotype, package, owner columns."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"depth": "3"})
    body = response.content.decode()
    assert "Container" in body
    assert "Technology" in body
    assert "payments-team" in body


@pytest.mark.django_db
def test_filter_package_excludes_context(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-14: package filter returns technology subset only."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"package": "technology"})
    body = response.content.decode()
    assert response.status_code == 200
    assert "Payment API" in body
    assert "Mobile App" not in body


@pytest.mark.django_db
def test_graph_json_returns_nodes_and_edges(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-15: graph JSON endpoint returns elements and edges."""
    client.force_login(view_browser_user)
    response = client.get(_browse_graph_url(), {"package": "technology"})
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert "elements" in payload
    assert "edges" in payload
    assert len(payload["elements"]) >= 1


@pytest.mark.django_db
def test_element_view_links_present(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-08: rows expose view-element links."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert 'data-testid="view-element-' in body


@pytest.mark.django_db
def test_viewer_sees_browser_without_create(client, view_browser_model):
    """VIEW-BROWSE-1-12: viewer role has browse without create affordance."""
    viewer = UserFactory(is_viewer=True)
    client.force_login(viewer)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="view-browse-page"' in body
    assert "Create Element" not in body


@pytest.mark.django_db
def test_navbar_primary_links(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-13: production navbar shows View Browser only."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert 'data-testid="nav-view-browser"' in body
    for dropped in ("nav-elements", "nav-relationships", "nav-changesets", "nav-runs"):
        assert f'data-testid="{dropped}"' not in body


@pytest.mark.django_db
def test_view_browser_three_panel_shell(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-16: three-panel explorer shell testids (graph mode)."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert response.status_code == 200
    for testid in (
        "browser-nav-panel",
        "browser-inspector-panel",
        "graph-cy-container",
        "browser-toggle-nav-panel",
        "browser-toggle-inspector-panel",
        "graph-replot-btn",
        "graph-zoom-in",
        "graph-zoom-out",
        "graph-zoom-fit",
        "browser-canvas-controls",
        "graph-node-count",
    ):
        assert f'data-testid="{testid}"' in body


@pytest.mark.django_db
def test_view_browser_full_height_layout(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-16: body uses yrg-view-browser layout class in graph mode."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert 'class="yrg-view-browser"' in body or 'class="yrg-view-browser ' in body


@pytest.mark.django_db
def test_view_browser_default_graph_mode(client, view_browser_user, view_browser_explorer_model):
    """Default presentation is graph mode with full-height layout."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    body = response.content.decode()
    assert "yrg-mode-graph" in body
    assert 'class="yrg-view-browser"' in body or 'class="yrg-view-browser ' in body
    assert 'data-testid="browser-nav-panel"' in body


@pytest.mark.django_db
def test_view_browser_table_mode_hides_graph_panels(
    client, view_browser_user, view_browser_explorer_model
):
    """Explicit ?mode=table SSR hides graph-only panels via yrg-mode-table."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"mode": "table"})
    body = response.content.decode()
    assert "yrg-mode-table" in body
    assert "yrg-graph-only" in body
    assert 'class="yrg-view-browser"' not in body


@pytest.mark.django_db
def test_mode_query_param_replaces_view(client, view_browser_user, view_browser_explorer_model):
    """W14-0: ?mode=table works; legacy ?view= remains aliased."""
    client.force_login(view_browser_user)
    mode_response = client.get(_browse_url(), {"mode": "table"})
    view_response = client.get(_browse_url(), {"view": "table"})
    assert mode_response.status_code == 200
    assert view_response.status_code == 200
    assert "yrg-mode-table" in mode_response.content.decode()
    assert "yrg-mode-table" in view_response.content.decode()
    assert 'name="mode"' in mode_response.content.decode()


@pytest.mark.django_db
def test_view_browser_navigator_element_tree(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-17/18: navigator shows traversal tree (graph mode)."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert 'data-testid="browser-model-name"' in body
    assert "Yggdrasil" in body
    assert 'data-testid="browser-element-tree"' in body
    assert 'data-testid="nav-element-' in body or 'data-testid="nav-toggle-' in body


@pytest.mark.django_db
def test_view_browser_navigator_lists_elements(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-19: navigator lists component elements at depth=1."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"stereotype": "component", "view": "graph"})
    body = response.content.decode()
    for name in ("auth", "graph", "munin", "web"):
        assert name in body


@pytest.mark.django_db
def test_view_browser_navigator_search_input(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-20: navigator search input present (graph mode)."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert 'data-testid="browser-search-input"' in body


@pytest.mark.django_db
def test_view_browse_log_story_happy(
    client, view_browser_user, view_browser_explorer_model, caplog
):
    """Log story: ViewBrowseView.get and build_view_browse_context beats."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(view_browser_user)
    client.get(_browse_url())
    client.get(_browse_graph_url())
    messages = " ".join(record.message for record in caplog.records)
    assert "ViewBrowseView.get" in messages
    assert "user_pk=" in messages
    assert "element_count=" in messages
    assert "build_view_browse_context" in messages
    assert "depth=" in messages
    assert "tree_root_count=" in messages
    assert "ViewBrowseGraphJsonView.get" in messages
    assert "node_count=" in messages
    assert "edges=" in messages


@pytest.mark.django_db
def test_htmx_partial_returns_results_only(client, view_browser_user, view_browser_model):
    """HTMX partial path returns self-contained results without breaking."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), HTTP_HX_REQUEST="true")
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="results-container"' in body
    assert 'data-testid="browser-nav-panel"' not in body


@pytest.mark.django_db
def test_inspector_element_partial_renders_properties(
    client, view_browser_user, view_browser_explorer_model
):
    """Inspector element embed returns properties without navbar."""
    from yggdrasil.graph.models import Element

    element = Element.objects.filter(model=view_browser_explorer_model, slug="munin").first()
    assert element is not None
    client.force_login(view_browser_user)
    response = client.get(
        reverse(
            "web:view_browse_inspector_element_model",
            kwargs={"model_slug": "yggdrasil", "pk": element.pk},
        )
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert f'data-testid="inspector-element-{element.pk}"' in body
    assert "munin" in body
    assert "Properties" in body
    assert "nav-view-browser" not in body
    assert f'data-testid="inspector-open-full-{element.pk}"' in body
    assert 'title="not Yet implemented"' in body
    assert "disabled" in body


@pytest.mark.django_db
def test_inspector_relationship_partial_renders_endpoints(
    client, view_browser_user, view_browser_explorer_model
):
    """Inspector relationship embed returns endpoints without navbar."""
    from yggdrasil.graph.models import Element, Relationship

    munin = Element.objects.get(model=view_browser_explorer_model, slug="munin")
    llm = Element.objects.get(model=view_browser_explorer_model, slug="llm")
    rel = Relationship.objects.filter(
        model=view_browser_explorer_model, source=munin, target=llm
    ).first()
    assert rel is not None
    client.force_login(view_browser_user)
    response = client.get(
        reverse(
            "web:view_browse_inspector_relationship_model",
            kwargs={"model_slug": "yggdrasil", "pk": rel.pk},
        )
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert f'data-testid="inspector-relationship-{rel.pk}"' in body
    assert "depends_on" in body
    assert "munin" in body
    assert "llm" in body
    assert "nav-view-browser" not in body


# -- W12: Model switcher (scenarios 48-54) --


@pytest.mark.django_db
def test_view_browse_switcher_lists_models(client, view_browser_user, two_model_fixture):
    """VIEW-BROWSE-1-48: switcher lists readable models."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url("yggdrasil") + "?mode=graph")
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="browser-model-switcher"' in body
    assert 'data-testid="browser-model-name"' in body
    assert 'data-testid="browser-model-option-yggdrasil"' in body
    assert 'data-testid="browser-model-option-payments"' in body
    assert "Yggdrasil" in body


@pytest.mark.django_db
def test_view_browse_redirect_302_to_default(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-49: unscoped /views/ redirects to default model."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    assert response.status_code == 302
    assert response["Location"].startswith("/models/yggdrasil/views/")


@pytest.mark.django_db
def test_view_browse_canonical_200(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-50: canonical browse URL includes model slug."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url("yggdrasil") + "?mode=graph")
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="browser-nav-panel"' in body
    assert "Yggdrasil" in body


@pytest.mark.django_db
def test_view_browse_unknown_model_404(client, view_browser_user):
    """VIEW-BROWSE-1-52: unknown model slug returns 404."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url("does-not-exist"))
    assert response.status_code == 404


@pytest.mark.django_db
def test_view_browse_zero_models_empty_state(client, db):
    """VIEW-BROWSE-1-53: zero models shows empty state and disables switcher."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    mm = ensure_c4_metamodel()
    YggdrasilModelFactory(name="Private", slug="private", metamodel=mm, owner_group=other_group)
    client.force_login(user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert response.status_code == 200
    assert "No models yet" in body
    assert 'data-testid="browser-model-switcher"' in body
    assert "disabled" in body


@pytest.mark.django_db
def test_view_browse_switcher_no_create_action(client, view_browser_user, two_model_fixture):
    """VIEW-BROWSE-1-54: switcher has no create-model action."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url("yggdrasil") + "?mode=graph")
    body = response.content.decode()
    assert response.status_code == 200
    assert "Create model" not in body


@pytest.mark.django_db
def test_view_browse_sets_model_cookie(client, view_browser_user, view_browser_model):
    """W12: canonical GET sets yggdrasil_model cookie."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url())
    assert response.status_code == 200
    assert response.cookies[browse_service.MODEL_COOKIE_NAME].value == "yggdrasil"


@pytest.mark.django_db
def test_view_browse_sets_session_model_id(client, view_browser_user, view_browser_model):
    """W12: canonical GET sets session model_id for other GUI screens."""
    client.force_login(view_browser_user)
    client.get(_browse_url())
    session = client.session
    assert session.get("model_id") == view_browser_model.pk


@pytest.mark.django_db
def test_view_browse_redirect_log_story_happy(
    client, view_browser_user, view_browser_model, caplog
):
    """W12 log story: redirect alias emits entry and exit beats."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(view_browser_user)
    client.get(reverse("web:view_browse"))
    assert_log_story(
        caplog,
        where="ViewBrowseRedirectView.get",
        beats={
            "entry": ["user_pk="],
            "exit": ["location=", "model_slug="],
        },
    )


@pytest.mark.django_db
def test_view_browse_redirect_log_story_zero_models(client, db, caplog):
    """W12 log story: zero-model branch on alias."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    mm = ensure_c4_metamodel()
    YggdrasilModelFactory(name="Private", slug="private", metamodel=mm, owner_group=other_group)
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(user)
    client.get(reverse("web:view_browse"))
    assert_log_story(
        caplog,
        where="ViewBrowseRedirectView.get",
        beats={
            "empty": ["empty_state=true"],
        },
    )


@pytest.mark.django_db
def test_view_browse_canonical_log_story_happy(
    client, view_browser_user, view_browser_model, caplog
):
    """W12 log story: canonical browse sets cookie and exits."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(view_browser_user)
    client.get(_browse_url())
    assert_log_story(
        caplog,
        where="ViewBrowseView.get",
        beats={
            "entry": ["user_pk=", "model_slug="],
            "cookie": ["cookie=", "model_slug="],
            "exit": ["element_count="],
        },
    )


@pytest.mark.django_db
def test_view_browse_canonical_log_story_reject(client, view_browser_user, caplog):
    """W12 log story: unknown slug validation beat."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(view_browser_user)
    client.get(_browse_url("does-not-exist"))
    assert_log_story(
        caplog,
        where="ViewBrowseView.get",
        beats={
            "reject": ["model not found"],
        },
    )


# -- W13: depth traversal (scenarios 55-60) --


@pytest.mark.django_db
def test_depth_slider_renders_graph_mode(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-55: depth slider visible in graph mode."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert 'data-testid="browser-depth-slider"' in body
    assert 'data-testid="browser-depth-value"' in body


@pytest.mark.django_db
def test_depth_1_hides_neighbors_in_navigator(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-18: component depth=1 hides Redis."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url(),
        {"view": "graph", "stereotype": "component", "depth": "1"},
    )
    body = response.content.decode()
    assert 'data-testid="nav-element-redis"' not in body
    assert "Redis" not in body or 'data-testid="nav-element-redis"' not in body


@pytest.mark.django_db
def test_depth_3_shows_redis_in_navigator(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-19b: component depth=3 shows Redis in navigator."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url(),
        {"view": "graph", "stereotype": "component", "depth": "3"},
    )
    body = response.content.decode()
    assert 'data-testid="nav-element-redis"' in body


@pytest.mark.django_db
def test_graph_json_respects_depth(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-56: graph JSON node set respects depth param."""
    client.force_login(view_browser_user)
    shallow = client.get(
        _browse_graph_url(),
        {"stereotype": "component", "depth": "1"},
    )
    deep = client.get(
        _browse_graph_url(),
        {"stereotype": "component", "depth": "3"},
    )
    shallow_count = len(json.loads(shallow.content)["elements"])
    deep_count = len(json.loads(deep.content)["elements"])
    assert deep_count > shallow_count


@pytest.mark.django_db
def test_table_respects_depth(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-58: table row count respects depth param."""
    client.force_login(view_browser_user)
    shallow = client.get(_browse_url(), {"depth": "1"})
    deep = client.get(_browse_url(), {"depth": "3"})
    shallow_body = shallow.content.decode()
    deep_body = deep.content.decode()
    assert shallow_body.count('data-testid="view-element-') < deep_body.count(
        'data-testid="view-element-'
    )


@pytest.mark.django_db
def test_view_browse_depth_log_story_happy(
    client, view_browser_user, view_browser_explorer_model, caplog
):
    """W13: depth beats in context build and graph JSON."""
    caplog.set_level(logging.INFO)
    client.force_login(view_browser_user)
    client.get(_browse_url(), {"depth": "2", "view": "graph", "stereotype": "component"})
    client.get(_browse_graph_url(), {"depth": "2", "stereotype": "component"})
    messages = " ".join(record.message for record in caplog.records)
    assert "depth=2" in messages
    assert "ViewBrowseGraphJsonView.get" in messages
    assert "node_count=" in messages


@pytest.mark.django_db
def test_navigator_partial_returns_tree_without_full_page(
    client, view_browser_user, view_browser_explorer_model
):
    """Depth slider refresh: partial=navigator returns tree HTML only."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url("yggdrasil"),
        {"partial": "navigator", "view": "graph", "stereotype": "component", "depth": "2"},
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="browser-nav-panel"' not in body
    assert 'id="elementTree"' not in body
    assert "yrg-tree-node" in body or 'data-testid="nav-element-' in body


@pytest.mark.django_db
def test_depth_change_with_view_graph_stays_in_graph_mode_ssr(
    client, view_browser_user, view_browser_explorer_model
):
    """Server must honour view=graph when depth changes (full reload fallback)."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url("yggdrasil"),
        {"view": "graph", "stereotype": "component", "depth": "3"},
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert 'class="yrg-browser-root yrg-mode-graph' in body or "yrg-mode-graph" in body
    assert 'data-testid="browser-depth-value"' in body
    assert "3 /" in body


@pytest.mark.django_db
def test_results_partial_via_query_param(client, view_browser_user, view_browser_model):
    """Clear-filters refresh: partial=results returns results container only."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url("yggdrasil"),
        {"partial": "results", "view": "graph"},
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="results-container"' in body
    assert 'data-element-count="' in body
    assert 'data-testid="browser-nav-panel"' not in body


@pytest.mark.django_db
def test_cleared_filters_with_view_graph_stays_graph_mode(
    client, view_browser_user, view_browser_explorer_model
):
    """Clear filters (full reload fallback) honours view=graph."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url("yggdrasil"),
        {"view": "graph", "package": "technology"},
    )
    assert response.status_code == 200
    response = client.get(_browse_url("yggdrasil"), {"view": "graph"})
    body = response.content.decode()
    assert response.status_code == 200
    assert "yrg-mode-graph" in body
