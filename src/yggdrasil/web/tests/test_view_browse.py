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
