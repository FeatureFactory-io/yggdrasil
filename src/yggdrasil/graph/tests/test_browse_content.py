"""Tests for graph browse_content (W15 field_map helpers)."""

from __future__ import annotations

import logging

from django.test import RequestFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_content


def test_parse_field_map_from_query() -> None:
    """W15: field_{stereotype}= params parse into field_map dict."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        [
            ("field_component", "name"),
            ("field_component", "owner"),
            ("field_container", "health"),
        ],
    )
    field_map = browse_content.parse_field_map_from_query(request.GET)
    assert field_map["component"] == ["name", "owner"]
    assert field_map["container"] == ["health"]


def test_field_path_label_properties() -> None:
    """Property paths get humanized labels."""
    assert browse_content.field_path_label("properties.jira_key") == "Jira key"


def test_format_node_label_from_paths() -> None:
    """Graph labels render Key: value lines."""
    element = {
        "name": "auth",
        "owner": "platform-team",
        "stereotype_slug": "component",
        "properties": {"jira_key": "YGG-1"},
    }
    label = browse_content.format_node_label_from_paths(
        element, ["name", "owner", "properties.jira_key"]
    )
    assert "Name: auth" in label
    assert "Owner: platform-team" in label
    assert "Jira key: YGG-1" in label


def test_build_view_field_sections_for_stereotypes() -> None:
    """Field sections appear for selected element and edge stereotypes."""
    sections = browse_content.build_view_field_sections(
        ["component"], ["depends_on"], {"component": ["name", "owner"]}
    )
    slugs = {section["slug"] for section in sections}
    assert slugs == {"component", "depends_on"}
    component = next(section for section in sections if section["slug"] == "component")
    assert component["checked_paths"] == ["name", "owner"]


def test_build_table_columns_from_field_map() -> None:
    """Table columns derive from field_map selections."""
    cols = browse_content.build_table_columns(
        element_stereotypes=["component"],
        field_map={"component": ["name", "owner", "health"]},
    )
    keys = [col["key"] for col in cols]
    assert keys[:2] == ["name", "stereotype"]
    assert "owner" in keys
    assert "health" in keys


def test_parse_field_map_log_story(caplog) -> None:
    """W15 log story: field_map parsed logs stereotype and path counts."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        [("field_component", "name")],
    )
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph"):
        browse_content.parse_field_map_from_query(request.GET)
    assert_log_story(
        caplog,
        where="browse_content.parse_field_map_from_query",
        beats={"processing": ["field_stereotypes=", "field_path_count="]},
    )


def test_format_node_label_log_story(caplog) -> None:
    """W15 log story: format_node_label_from_paths logs element_id and path_count."""
    element = {"id": 42, "name": "auth", "owner": "platform-team"}
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph"):
        browse_content.format_node_label_from_paths(element, ["name", "owner"])
    assert_log_story(
        caplog,
        where="browse_content.format_node_label_from_paths",
        beats={"processing": ["element_id=", "path_count="]},
    )


def test_browse_content_log_story_happy(caplog) -> None:
    """W15 log story alias: parse_field_map covers field_map resolution beats."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        [
            ("field_component", "name"),
            ("field_component", "owner"),
        ],
    )
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph"):
        field_map = browse_content.parse_field_map_from_query(request.GET)
    assert field_map["component"] == ["name", "owner"]
    assert_log_story(
        caplog,
        where="browse_content.parse_field_map_from_query",
        beats={"processing": ["field_stereotypes=", "field_path_count="]},
    )
