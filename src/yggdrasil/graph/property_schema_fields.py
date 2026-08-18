"""Helpers for metamodel ``property_schema`` → browse field paths and inspector rows."""

from __future__ import annotations

from typing import Any

BASE_ELEMENT_FIELDS: list[dict[str, str]] = [
    {"path": "name", "label": "Name"},
    {"path": "owner", "label": "Owner"},
    {"path": "health", "label": "Health"},
    {"path": "package", "label": "Package"},
]

BASE_RELATIONSHIP_FIELDS: list[dict[str, str]] = [
    {"path": "stereotype", "label": "Stereotype"},
]


def _label_for_property_key(key: str, spec: Any) -> str:
    """Human label from JSON Schema property spec or key name."""
    if isinstance(spec, dict):
        title = spec.get("title")
        if title:
            return str(title)
    return key.replace("_", " ").title()


def field_paths_from_property_schema(schema: dict[str, Any] | None) -> list[dict[str, str]]:
    """
    Return browse field paths derived from a stereotype ``property_schema``.

    :param schema: JSON Schema object from ``Stereotype.property_schema``.
    :return: Rows with ``path`` (e.g. ``properties.actor_id``) and ``label``.
    """
    if not schema:
        return []
    properties = schema.get("properties") or {}
    if not isinstance(properties, dict):
        return []
    rows: list[dict[str, str]] = []
    for key in sorted(properties.keys()):
        spec = properties[key]
        rows.append(
            {
                "path": f"properties.{key}",
                "label": _label_for_property_key(str(key), spec),
                "property_key": str(key),
            }
        )
    return rows


def merge_field_definitions(
    static_fields: list[dict[str, str]],
    schema: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """
    Merge static browse fields with dynamic ``property_schema`` paths.

    :param static_fields: Hard-coded defaults for a stereotype slug.
    :param schema: Stereotype ``property_schema`` JSON.
    :return: De-duplicated ordered field rows.
    """
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in static_fields + field_paths_from_property_schema(schema):
        path = row["path"]
        if path in seen:
            continue
        seen.add(path)
        merged.append({"path": path, "label": row["label"]})
    return merged


def inspector_property_rows(
    *,
    properties: dict[str, Any] | None,
    property_schema: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """
    Build ordered inspector property rows with labels and display values.

    Schema keys appear even when the stored value is empty (shown as em dash).

    :param properties: Element or relationship ``properties`` JSON object.
    :param property_schema: Stereotype ``property_schema`` for label ordering.
    :return: Rows with ``key``, ``label``, and ``value`` strings.
    """
    props = properties if isinstance(properties, dict) else {}
    schema_paths = field_paths_from_property_schema(property_schema)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for field in schema_paths:
        key = field.get("property_key") or field["path"].split(".", 1)[-1]
        seen.add(key)
        raw = props.get(key)
        value = "" if raw is None else str(raw)
        rows.append({"key": key, "label": field["label"], "value": value})

    for key in sorted(props.keys()):
        if key in seen:
            continue
        raw = props[key]
        rows.append(
            {
                "key": str(key),
                "label": str(key).replace("_", " ").title(),
                "value": "" if raw is None else str(raw),
            }
        )
    return rows
