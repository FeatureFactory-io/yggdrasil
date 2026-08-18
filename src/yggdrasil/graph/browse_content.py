"""
Browse content helpers — field_map parsing and canvas display (W15).

Ported from mockup-validated Filters-first View Browser UX.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("yggdrasil.graph")

TABLE_COLUMN_LABELS: dict[str, str] = {
    "name": "Name",
    "stereotype": "Stereotype",
    "owner": "Owner",
    "health": "Health",
    "package": "Package",
    "source": "Source",
    "properties.jira_key": "Jira key",
    "properties.version": "Version",
}

STEREOTYPE_FIELD_SCHEMA: dict[str, list[dict[str, str]]] = {
    "system": [
        {"path": "name", "label": "Name"},
        {"path": "owner", "label": "Owner"},
        {"path": "package", "label": "Package"},
    ],
    "container": [
        {"path": "name", "label": "Name"},
        {"path": "owner", "label": "Owner"},
        {"path": "health", "label": "Health"},
        {"path": "properties.version", "label": "Version"},
    ],
    "component": [
        {"path": "name", "label": "Name"},
        {"path": "owner", "label": "Owner"},
        {"path": "health", "label": "Health"},
        {"path": "properties.version", "label": "Version"},
        {"path": "properties.jira_key", "label": "Jira key"},
    ],
    "person": [
        {"path": "name", "label": "Name"},
        {"path": "package", "label": "Package"},
    ],
    "depends_on": [
        {"path": "stereotype", "label": "Stereotype"},
        {"path": "properties.protocol", "label": "Protocol"},
    ],
    "calls": [
        {"path": "stereotype", "label": "Stereotype"},
        {"path": "properties.protocol", "label": "Protocol"},
    ],
    "uses": [
        {"path": "stereotype", "label": "Stereotype"},
    ],
}


def parse_field_map_from_query(query: Any) -> dict[str, list[str]]:
    """
    Parse ``field_{stereotype}`` repeated query params into a field map.

    :param query: Query mapping (``request.GET``).
    :return: Stereotype slug → ordered field paths.
    """
    field_map: dict[str, list[str]] = {}
    getlist = getattr(query, "getlist", None)
    for key in query:
        if not str(key).startswith("field_"):
            continue
        slug = str(key)[6:].lower()
        if not slug:
            continue
        values = getlist(key) if getlist else [query.get(key)]
        for raw in values:
            val = str(raw).strip()
            if val:
                field_map.setdefault(slug, []).append(val)
    logger.info(
        "browse_content.parse_field_map_from_query | processing | field_stereotypes=%s field_path_count=%s",
        len(field_map),
        sum(len(paths) for paths in field_map.values()),
    )
    return field_map


def field_path_label(path: str) -> str:
    """
    Human-readable label for a Content field path.

    :param path: Element field path. Example: ``properties.jira_key``.
    :return: Display label for graph ``Key: value`` lines.
    """
    if path in TABLE_COLUMN_LABELS:
        return TABLE_COLUMN_LABELS[path]
    if path.startswith("properties."):
        prop = path.split(".", 1)[1]
        return prop.replace("_", " ").title()
    return path.replace("_", " ").title()


def element_field_value(element: dict[str, Any], path: str) -> str:
    """
    Resolve a dot-path field on an element summary dict.

    :param element: Element row dict from browse_service.
    :param path: Field path relative to element root.
    :return: Display string or empty when missing.
    """
    if path == "name":
        return str(element.get("name", ""))
    if path == "owner":
        return str(element.get("owner") or "")
    if path == "health":
        return str(element.get("health", ""))
    if path == "stereotype":
        return str(element.get("stereotype", ""))
    if path == "package":
        return str(element.get("package", ""))
    if path == "source":
        return str(element.get("source", ""))
    if path.startswith("properties."):
        prop_key = path.split(".", 1)[1]
        props = element.get("properties") or {}
        return str(props.get(prop_key, ""))
    return str(element.get(path, ""))


def format_node_label_from_paths(element: dict[str, Any], field_paths: list[str]) -> str:
    """
    Build in-node graph label lines as ``Key: value`` for each visible field.

    :param element: Element summary dict.
    :param field_paths: Ordered paths from active View ``field_map``.
    :return: Newline-separated label for Cytoscape node.
    """
    lines: list[str] = []
    for path in field_paths:
        value = element_field_value(element, path)
        if not value:
            continue
        lines.append(f"{field_path_label(path)}: {value}")
    if lines:
        return "\n".join(lines)
    name = element_field_value(element, "name") or "—"
    return f"{field_path_label('name')}: {name}"


def build_table_columns(
    *,
    element_stereotypes: list[str],
    field_map: dict[str, list[str]],
) -> list[dict[str, str]]:
    """
    Derive table columns from stereotype field selections in the active View.

    :param element_stereotypes: Selected element stereotype slugs.
    :param field_map: Stereotype slug → visible field paths.
    :return: Column metadata with ``key`` and ``label``.
    """
    cols = ["name", "stereotype"]
    seen = set(cols)
    for stereotype in element_stereotypes or list(field_map.keys()):
        for path in field_map.get(stereotype, []):
            if path not in seen:
                seen.add(path)
                cols.append(path)
    if len(cols) <= 2:
        cols.extend(["owner", "package"])
    return [
        {"key": key, "label": TABLE_COLUMN_LABELS.get(key, field_path_label(key))} for key in cols
    ]


def build_view_field_sections(
    element_stereotypes: list[str],
    relationship_stereotypes: list[str],
    selected_fields: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """
    Build stereotype-grouped field checklists for the Filters panel.

    :param element_stereotypes: Selected element stereotype slugs.
    :param relationship_stereotypes: Selected edge stereotype slugs.
    :param selected_fields: Stereotype slug → checked field paths; defaults all on.
    :return: Section dicts for template rendering.
    """
    selected_fields = selected_fields or {}
    sections: list[dict[str, Any]] = []
    for slug in element_stereotypes:
        fields = STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "name", "label": "Name"}])
        checked = selected_fields.get(slug) or [row["path"] for row in fields]
        sections.append(
            {
                "kind": "element",
                "slug": slug,
                "label": slug.replace("_", " ").title(),
                "fields": fields,
                "checked_paths": checked,
            }
        )
    for slug in relationship_stereotypes:
        fields = STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "stereotype", "label": "Stereotype"}])
        checked = selected_fields.get(slug) or [row["path"] for row in fields]
        sections.append(
            {
                "kind": "relationship",
                "slug": slug,
                "label": slug.replace("_", " "),
                "fields": fields,
                "checked_paths": checked,
            }
        )
    return sections


def field_map_for_element(element: dict[str, Any], field_map: dict[str, list[str]]) -> list[str]:
    """
    Resolve visible field paths for one element using its stereotype slug.

    :param element: Element row with ``stereotype_slug``.
    :param field_map: Active field map from params or saved View.
    :return: Field paths for label formatting.
    """
    slug = str(element.get("stereotype_slug") or "").lower()
    paths = list(field_map.get(slug) or [])
    if paths:
        return paths
    schema = STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "name"}])
    return [row["path"] for row in schema]


def table_cell_display(element: dict[str, Any], column_key: str) -> str:
    """
    Resolve a table cell display value for a column path.

    :param element: Element row dict.
    :param column_key: Field path from table column list.
    :return: Display string or em dash when empty.
    """
    value = element_field_value(element, column_key)
    return value if value else "—"
