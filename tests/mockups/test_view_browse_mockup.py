"""Tests for VIEW-BROWSE-1 mockup Views + Filters panel helpers."""

from __future__ import annotations

import pytest
from django.test import RequestFactory
from django.urls import reverse
from mockups.views import (
    MOCK_BROWSE_VIEWS,
    MOCK_VIEW_BROWSER_ELEMENTS,
    MOCK_VIEW_BROWSER_RELATIONSHIPS,
    build_package_scoped_filter_options,
    build_view_field_sections,
    enrich_mock_canvas_rows,
    field_map_to_content_display,
    filter_mock_elements,
    format_mock_edge_label_for_relationship,
    format_mock_node_label_for_element,
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
    assert params["packages"] == ["application"]
    assert params["element_stereotypes"] == ["component"]
    assert params["depth"] == 2
    assert params["mode"] == "graph"
    assert params["loaded_view_name"] == MOCK_BROWSE_VIEWS[0]["name"]


def test_parse_mode_query_param() -> None:
    factory = RequestFactory()
    request = factory.get("/mockups/view/browse/", {"mode": "table", "depth": "3"})
    params = parse_mock_browse_params(request)
    assert params["mode"] == "table"
    assert params["depth"] == 3


def test_parse_multi_select_filters() -> None:
    factory = RequestFactory()
    request = factory.get(
        "/mockups/view/browse/",
        [("package", "application"), ("package", "technology"), ("stereotype", "component")],
    )
    params = parse_mock_browse_params(request)
    assert params["packages"] == ["application", "technology"]
    assert params["element_stereotypes"] == ["component"]


def test_filter_mock_elements_by_stereotype() -> None:
    params = parse_mock_browse_params(RequestFactory().get("/", {"stereotype": "component"}))
    assert params["element_stereotypes"] == ["component"]
    filtered = filter_mock_elements(MOCK_VIEW_BROWSER_ELEMENTS, params)
    assert filtered
    assert all(el["stereotype"].lower() == "component" for el in filtered)


def test_build_view_field_sections_for_stereotypes() -> None:
    sections = build_view_field_sections(["component"], ["depends_on"])
    assert len(sections) == 2
    assert sections[0]["slug"] == "component"
    assert sections[1]["slug"] == "depends_on"


def test_build_package_scoped_filter_options_narrows_by_package() -> None:
    scoped = build_package_scoped_filter_options(
        MOCK_VIEW_BROWSER_ELEMENTS,
        MOCK_VIEW_BROWSER_RELATIONSHIPS,
        ["application"],
    )
    element_slugs = {row["slug"] for row in scoped["stereotypes"]}
    assert "component" in element_slugs
    assert "container" in element_slugs
    assert "person" not in element_slugs


def test_build_package_scoped_filter_options_all_when_no_package() -> None:
    scoped = build_package_scoped_filter_options(
        MOCK_VIEW_BROWSER_ELEMENTS,
        MOCK_VIEW_BROWSER_RELATIONSHIPS,
        [],
    )
    element_slugs = {row["slug"] for row in scoped["stereotypes"]}
    assert "person" in element_slugs
    assert scoped["relationship_stereotypes"]


def test_format_mock_node_label_includes_selected_fields() -> None:
    munin = next(el for el in MOCK_VIEW_BROWSER_ELEMENTS if el["slug"] == "munin")
    display = field_map_to_content_display(
        {"component": ["name", "owner", "health", "properties.jira_key"]},
        ["component"],
        [],
    )
    label = format_mock_node_label_for_element(munin, display)
    assert "Name: munin" in label
    assert "Owner: platform-team" in label
    assert "Jira key: YGG-142" in label


def test_format_mock_edge_label_includes_protocol() -> None:
    rel = next(r for r in MOCK_VIEW_BROWSER_RELATIONSHIPS if r["edge_stereotype"] == "calls")
    display = field_map_to_content_display(
        {"calls": ["stereotype", "properties.protocol"]},
        [],
        ["calls"],
    )
    label = format_mock_edge_label_for_relationship(rel, display)
    assert "calls" in label
    assert "HTTP" in label or "protocol" in label


def test_enrich_mock_canvas_rows_adds_labels_and_cells() -> None:
    params = parse_mock_browse_params(
        RequestFactory().get(
            "/", {"stereotype": "component", "browse_view": MOCK_BROWSE_VIEWS[0]["slug"]}
        )
    )
    elements = filter_mock_elements(MOCK_VIEW_BROWSER_ELEMENTS, params)
    field_map = params["field_map"]
    display = field_map_to_content_display(
        field_map,
        params["element_stereotypes"],
        params["relationship_stereotypes"],
    )
    from mockups.views import build_table_columns_from_params

    table_columns = build_table_columns_from_params(params)
    rows, rels = enrich_mock_canvas_rows(
        elements, MOCK_VIEW_BROWSER_RELATIONSHIPS[:3], table_columns, display
    )
    assert rows[0]["node_label"]
    assert rows[0]["table_cells"]
    assert rels[0]["edge_label"]


@pytest.mark.django_db
def test_mockup_browse_renders_filters_first_view(client, settings) -> None:
    settings.DEBUG = True
    slug = MOCK_BROWSE_VIEWS[0]["slug"]
    response = client.get(reverse("mockup_view_browse"), {"browse_view": slug})
    assert response.status_code == 200
    html = response.content.decode()
    assert 'data-testid="filters-toggle"' in html
    assert 'data-testid="active-view-name"' in html
    assert MOCK_BROWSE_VIEWS[0]["name"] in html
    assert 'data-testid="filter-edge-stereotype"' in html
    assert 'data-testid="apply-filters-btn"' in html
    assert 'data-testid="view-field-sections"' in html
    assert 'id="mock-filter-catalog"' in html


@pytest.mark.django_db
def test_mockup_browse_canvas_payload_includes_elements(client, settings) -> None:
    settings.DEBUG = True
    slug = MOCK_BROWSE_VIEWS[0]["slug"]
    response = client.get(reverse("mockup_view_browse"), {"browse_view": slug})
    html = response.content.decode()
    assert 'id="mock-canvas-data"' in html
    import json
    import re

    match = re.search(
        r'<script id="mock-canvas-data" type="application/json">(.+?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "mock-canvas-data script tag missing"
    payload = json.loads(match.group(1))
    assert len(payload["elements"]) >= 9
    assert payload["elements"][0].get("node_label")


@pytest.mark.django_db
def test_mockup_browse_field_sections_when_stereotypes_selected(client, settings) -> None:
    settings.DEBUG = True
    response = client.get(
        reverse("mockup_view_browse"),
        {"stereotype": "component", "edge_stereotype": "depends_on"},
    )
    html = response.content.decode()
    assert 'data-testid="view-fields-component"' in html
    assert 'data-testid="view-fields-depends_on"' in html


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
