"""Web tests for VIEW-BROWSE-1 Filters-first content (W15)."""

from __future__ import annotations

import logging

import pytest
from django.http import QueryDict
from django.urls import reverse
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_view_service
from yggdrasil.graph.models import BrowseView


def _browse_url(model_slug: str = "yggdrasil") -> str:
    return reverse("web:view_browse_model", kwargs={"model_slug": model_slug})


def _graph_url(model_slug: str = "yggdrasil") -> str:
    return reverse("web:view_browse_graph_model", kwargs={"model_slug": model_slug})


@pytest.mark.django_db
def test_filter_panel_lists_custom_property_schema_fields(
    client, view_browser_user, view_browser_explorer_model
):
    """Regression #101: Filters panel exposes metamodel custom property paths."""
    from yggdrasil.graph.models import Stereotype

    Stereotype.objects.update_or_create(
        metamodel=view_browser_explorer_model.metamodel,
        slug="actor",
        defaults={
            "name": "Actor",
            "is_edge": False,
            "property_schema": {
                "type": "object",
                "properties": {
                    "actor_id": {"type": "string", "title": "Actor ID"},
                    "persona_name": {"type": "string"},
                },
            },
        },
    )
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"stereotype": "actor"})
    body = response.content.decode()
    assert response.status_code == 200
    assert 'data-testid="view-fields-actor"' in body
    assert 'data-testid="view-field-actor-properties.actor_id"' in body
    assert 'data-testid="view-field-actor-properties.persona_name"' in body


@pytest.mark.django_db
def test_field_sections_render_when_stereotype_selected(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-69: field sections SSR when element stereotype selected."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"stereotype": "component"})
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="view-field-sections"' in body
    assert 'data-testid="view-fields-component"' in body


@pytest.mark.django_db
def test_field_query_params_select_visible_fields(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-72: repeated field_component params render checked fields."""
    client.force_login(view_browser_user)
    response = client.get(
        _browse_url(),
        [
            ("stereotype", "component"),
            ("field_component", "name"),
            ("field_component", "owner"),
        ],
    )
    assert response.status_code == 200
    assert 'data-testid="view-fields-component"' in response.content.decode()


@pytest.mark.django_db
def test_graph_json_applies_field_map_labels(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-70: graph JSON node labels include Key: value lines."""
    client.force_login(view_browser_user)
    response = client.get(
        _graph_url(),
        [
            ("stereotype", "component"),
            ("field_component", "name"),
            ("field_component", "owner"),
            ("depth", "2"),
        ],
    )
    assert response.status_code == 200
    payload = response.json()
    labels = [node["data"]["label"] for node in payload["elements"]]
    munin_label = next(label for label in labels if "munin" in label.lower())
    assert "Name: munin" in munin_label
    assert "Owner: platform-team" in munin_label


@pytest.mark.django_db
def test_save_view_persists_field_map(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-73: save View stores content.field_map in payload."""
    client.force_login(view_browser_user)
    save_url = reverse("web:view_browse_save", kwargs={"model_slug": "yggdrasil"})
    post_data = QueryDict(mutable=True)
    post_data.setlist(
        "stereotype",
        ["component"],
    )
    post_data.setlist("field_component", ["owner"])
    post_data.update({"name": "Owners visible", "depth": "2", "mode": "graph"})
    response = client.post(save_url, post_data)
    assert response.status_code == 302
    view = BrowseView.objects.get(slug="owners-visible")
    field_map = view.payload.get("content", {}).get("field_map", {})
    assert field_map.get("component") == ["owner"]


@pytest.mark.django_db
def test_load_named_view_expands_field_map(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-74: browse_view= expands field_map into graph labels."""
    browse_view_service.save_view(
        view_browser_user,
        view_browser_explorer_model,
        name="Application components",
        payload={
            "filters": {
                "packages": [],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 2},
            "presentation": "graph",
            "content": {"field_map": {"component": ["name", "owner"]}},
        },
    )
    client.force_login(view_browser_user)
    response = client.get(
        _graph_url(),
        {"browse_view": "application-components", "depth": "2"},
    )
    assert response.status_code == 200
    labels = [node["data"]["label"] for node in response.json()["elements"]]
    auth_label = next(label for label in labels if "auth" in label.lower())
    assert "Owner: platform-team" in auth_label


@pytest.mark.django_db
def test_table_mode_saved_view_omits_viewport_json(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-76: table presentation must not embed graph viewport JSON."""
    browse_view_service.save_view(
        view_browser_user,
        view_browser_explorer_model,
        name="table only",
        payload={
            "filters": {
                "packages": [],
                "element_stereotypes": [],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 1},
            "presentation": "table",
            "viewport": {"zoom": 2.0, "pan": {"x": 1, "y": 2}},
        },
    )
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"browse_view": "table-only"})
    body = response.content.decode()
    assert response.status_code == 200
    assert 'id="loaded-viewport"' not in body
    assert "browser-canvas-controls" in body


@pytest.mark.django_db
def test_graph_json_shows_jira_key_label(client, view_browser_user, view_browser_explorer_model):
    """VIEW-BROWSE-1-78: field_map includes properties.jira_key on munin."""
    client.force_login(view_browser_user)
    response = client.get(
        _graph_url(),
        [
            ("stereotype", "component"),
            ("field_component", "properties.jira_key"),
            ("depth", "2"),
        ],
    )
    payload = response.json()
    labels = [node["data"]["label"] for node in payload["elements"]]
    assert any("Jira key: YGG-142" in label for label in labels), labels


@pytest.mark.django_db
def test_package_scoped_stereotypes_exclude_context_person(
    client, view_browser_user, view_browser_explorer_model
):
    """VIEW-BROWSE-1-79: application package scopes stereotype options."""
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"package": "application", "mode": "graph"})
    body = response.content.decode()
    assert 'value="component"' in body
    assert (
        'value="person"'
        not in body.split('data-testid="filter-stereotype"')[1].split("</select>")[0]
    )


@pytest.mark.django_db
def test_view_browse_content_log_story_happy(
    client, view_browser_user, view_browser_explorer_model, caplog
):
    """W15 log story: graph JSON exit includes field_map_stereotypes and node_count."""
    client.force_login(view_browser_user)
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        response = client.get(
            _graph_url(),
            [
                ("stereotype", "component"),
                ("field_component", "name"),
                ("field_component", "owner"),
                ("depth", "2"),
            ],
        )
    assert response.status_code == 200
    assert_log_story(
        caplog,
        where="ViewBrowseGraphJsonView.get",
        beats={
            "exit": ["field_map_stereotypes=", "node_count="],
        },
    )
