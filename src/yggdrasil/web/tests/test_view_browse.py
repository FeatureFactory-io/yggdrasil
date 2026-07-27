"""VIEW-BROWSE-1 web view tests."""

from __future__ import annotations

import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_view_browser_shell_testids(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-01: shell exposes filter panel and table/graph toggles."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="view-browse-page"' in body
    assert 'data-testid="filters-toggle"' in body
    assert 'data-testid="filter-package"' in body
    assert 'data-testid="toggle-table"' in body
    assert 'data-testid="toggle-graph"' in body
    assert 'data-testid="results-container"' in body


@pytest.mark.django_db
def test_default_view_shows_elements(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-02: default view lists six seeded elements."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert response.status_code == 200
    for name in (
        "Payment API",
        "Notification Service",
        "Order Domain",
        "Fulfillment Worker",
        "PostgreSQL",
        "Mobile App",
    ):
        assert name in body


@pytest.mark.django_db
def test_table_columns_present(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-03: table shows stereotype, package, owner columns."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert "Container" in body
    assert "Technology" in body
    assert "payments-team" in body


@pytest.mark.django_db
def test_filter_package_excludes_context(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-14: package filter returns technology subset only."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"), {"package": "technology"})
    body = response.content.decode()
    assert response.status_code == 200
    assert "Payment API" in body
    assert "Mobile App" not in body


@pytest.mark.django_db
def test_graph_json_returns_nodes_and_edges(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-15: graph JSON endpoint returns elements and edges."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse_graph"), {"package": "technology"})
    assert response.status_code == 200
    payload = json.loads(response.content)
    assert "elements" in payload
    assert "edges" in payload
    assert len(payload["elements"]) >= 1


@pytest.mark.django_db
def test_element_view_links_present(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-08: rows expose view-element links."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert 'data-testid="view-element-' in body


@pytest.mark.django_db
def test_viewer_sees_browser_without_create(client, view_browser_model):
    """VIEW-BROWSE-1-12: viewer role has browse without create affordance."""
    from tests.fixtures.factories import UserFactory

    viewer = UserFactory(is_viewer=True)
    client.force_login(viewer)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="view-browse-page"' in body
    assert "Create Element" not in body


@pytest.mark.django_db
def test_navbar_primary_links(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-13: primary navbar testids visible."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert 'data-testid="nav-view-browser"' in body
    assert 'data-testid="nav-elements"' in body
    assert 'data-testid="nav-relationships"' in body
    assert 'data-testid="nav-changesets"' in body
    assert 'data-testid="nav-runs"' in body


GRAPH_URL = reverse("web:view_browse") + "?view=graph"


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
def test_view_browser_table_mode_hides_graph_panels(
    client, view_browser_user, view_browser_explorer_model
):
    """Default table mode SSR hides graph-only panels via yrg-mode-table."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
    body = response.content.decode()
    assert "yrg-mode-table" in body
    assert "yrg-graph-only" in body
    assert 'class="yrg-view-browser"' not in body


@pytest.mark.django_db
def test_view_browser_navigator_package_tree(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-17/18: navigator shows model name and package toggles (graph mode)."""
    client.force_login(view_browser_user)
    response = client.get(GRAPH_URL)
    body = response.content.decode()
    assert 'data-testid="browser-model-name"' in body
    assert "Yggdrasil" in body
    for slug in ("context", "application", "technology"):
        assert f'data-testid="package-toggle-{slug}"' in body


@pytest.mark.django_db
def test_view_browser_navigator_lists_elements(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-19: navigator lists Application package elements."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"))
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
    import logging

    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.force_login(view_browser_user)
    client.get(reverse("web:view_browse"))
    client.get(reverse("web:view_browse_graph"))
    messages = " ".join(r.message for r in caplog.records)
    assert "ViewBrowseView.get" in messages
    assert "user_pk=" in messages
    assert "element_count=" in messages
    assert "build_view_browse_context" in messages
    assert "package_count=" in messages
    assert "ViewBrowseGraphJsonView.get" in messages
    assert "nodes=" in messages
    assert "edges=" in messages


@pytest.mark.django_db
def test_htmx_partial_returns_results_only(client, view_browser_user, view_browser_model):
    """HTMX partial path returns self-contained results without breaking."""
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse"), HTTP_HX_REQUEST="true")
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
    response = client.get(reverse("web:view_browse_inspector_element", args=[element.pk]))
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="inspector-element-' + str(element.pk) + '"' in body
    assert "munin" in body
    assert "Properties" in body
    assert "nav-view-browser" not in body


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
    response = client.get(reverse("web:view_browse_inspector_relationship", args=[rel.pk]))
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="inspector-relationship-' + str(rel.pk) + '"' in body
    assert "depends_on" in body
    assert "munin" in body
    assert "llm" in body
    assert "nav-view-browser" not in body
