"""Tests for VIEW-BROWSE-1 mockup Views v1 helpers."""

from __future__ import annotations

import pytest
from django.test import RequestFactory
from django.urls import reverse
from mockups.views import (
    MOCK_BROWSE_VIEWS,
    MOCK_VIEW_BROWSER_ELEMENTS,
    filter_mock_elements,
    parse_mock_browse_params,
    slugify_view_name,
)


def test_slugify_view_name() -> None:
    assert slugify_view_name("Payment capability review") == "payment-capability-review"


def test_parse_browse_view_expands_payload() -> None:
    factory = RequestFactory()
    slug = MOCK_BROWSE_VIEWS[0]["slug"]
    request = factory.get("/mockups/view/browse/", {"browse_view": slug})
    params = parse_mock_browse_params(request)
    assert params["browse_view"] == slug
    assert params["stereotype"] == "component"
    assert params["depth"] == 2
    assert params["mode"] == "graph"
    assert params["loaded_view_name"] == MOCK_BROWSE_VIEWS[0]["name"]


def test_parse_mode_query_param() -> None:
    factory = RequestFactory()
    request = factory.get("/mockups/view/browse/", {"mode": "table", "depth": "3"})
    params = parse_mock_browse_params(request)
    assert params["mode"] == "table"
    assert params["depth"] == 3


def test_filter_mock_elements_by_stereotype() -> None:
    params = parse_mock_browse_params(RequestFactory().get("/", {"stereotype": "component"}))
    filtered = filter_mock_elements(MOCK_VIEW_BROWSER_ELEMENTS, params)
    assert filtered
    assert all(el["stereotype"].lower() == "component" for el in filtered)


@pytest.mark.django_db
def test_mockup_browse_renders_views_v1_shell(client, settings) -> None:
    settings.DEBUG = True
    response = client.get(reverse("mockup_view_browse"))
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-testid="views-dropdown"' in html
    assert 'id="saveViewModal"' in html
    assert "mockup-view-browser.js" in html


@pytest.mark.django_db
def test_mockup_browse_view_slug_expansion(client, settings) -> None:
    settings.DEBUG = True
    slug = MOCK_BROWSE_VIEWS[0]["slug"]
    response = client.get(reverse("mockup_view_browse"), {"browse_view": slug})
    assert response.status_code == 200
    assert 'data-testid="browser-depth-value"' in response.content.decode()
    assert b"2 / 5" in response.content
