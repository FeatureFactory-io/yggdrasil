"""Tests for property_schema field helpers."""

from __future__ import annotations

from yggdrasil.graph.property_schema_fields import (
    field_paths_from_property_schema,
    inspector_property_rows,
    merge_field_definitions,
)


def test_field_paths_from_property_schema_orders_keys() -> None:
    """Schema properties become properties.* browse paths."""
    schema = {
        "type": "object",
        "properties": {
            "actor_id": {"type": "string", "title": "Actor ID"},
            "persona_name": {"type": "string"},
        },
    }
    rows = field_paths_from_property_schema(schema)
    assert [row["path"] for row in rows] == [
        "properties.actor_id",
        "properties.persona_name",
    ]
    assert rows[0]["label"] == "Actor ID"
    assert rows[1]["label"] == "Persona Name"


def test_inspector_property_rows_includes_schema_and_extra_keys() -> None:
    """Inspector rows merge schema order with ad-hoc stored properties."""
    rows = inspector_property_rows(
        properties={"persona_name": "Manager", "legacy_note": "keep"},
        property_schema={
            "type": "object",
            "properties": {
                "actor_id": {"type": "string"},
                "persona_name": {"type": "string"},
            },
        },
    )
    labels = [row["label"] for row in rows]
    assert labels.index("Actor Id") < labels.index("Persona Name")
    assert "Legacy Note" in labels
    persona = next(row for row in rows if row["key"] == "persona_name")
    assert persona["value"] == "Manager"
    actor = next(row for row in rows if row["key"] == "actor_id")
    assert actor["value"] == ""


def test_merge_field_definitions_deduplicates_paths() -> None:
    """Static and schema paths merge without duplicates."""
    static = [{"path": "name", "label": "Name"}, {"path": "properties.version", "label": "Version"}]
    schema = {"type": "object", "properties": {"version": {"type": "string"}, "jira_key": {}}}
    merged = merge_field_definitions(static, schema)
    paths = [row["path"] for row in merged]
    assert paths.count("properties.version") == 1
    assert "properties.jira_key" in paths
