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
    if field_map:
        logger.info(
            "browse_content.parse_field_map_from_query | branch | reason=populated "
            "field_stereotypes=%s",
            sorted(field_map),
        )
    else:
        logger.info(
            "browse_content.parse_field_map_from_query | branch | reason=empty",
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
    element_id = element.get("id", "")
    logger.info(
        "browse_content.format_node_label_from_paths | processing | element_id=%s path_count=%s",
        element_id,
        len(field_paths),
    )
    if lines:
        logger.info(
            "browse_content.format_node_label_from_paths | exit | element_id=%s "
            "line_count=%s reason=populated_label",
            element_id,
            len(lines),
        )
        return "\n".join(lines)
    name = element_field_value(element, "name") or "—"
    logger.info(
        "browse_content.format_node_label_from_paths | exit | element_id=%s "
        "line_count=1 reason=fallback_name",
        element_id,
    )
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
        logger.info(
            "browse_content.build_table_columns | branch | reason=default_columns "
            "stereotype_count=%s",
            len(element_stereotypes),
        )
        cols.extend(["owner", "package"])
    else:
        logger.info(
            "browse_content.build_table_columns | branch | reason=field_map_columns "
            "stereotype_count=%s field_map_keys=%s",
            len(element_stereotypes),
            sorted(field_map),
        )
    columns = [
        {"key": key, "label": TABLE_COLUMN_LABELS.get(key, field_path_label(key))} for key in cols
    ]
    logger.info(
        "browse_content.build_table_columns | exit | column_count=%s",
        len(columns),
    )
    return columns


def _field_section(
    *,
    kind: str,
    slug: str,
    fields: list[dict[str, str]],
    selected_fields: dict[str, list[str]],
) -> dict[str, Any]:
    """Build one stereotype field checklist section."""
    checked = selected_fields.get(slug) or [row["path"] for row in fields]
    label = slug.replace("_", " ").title() if kind == "element" else slug.replace("_", " ")
    return {
        "kind": kind,
        "slug": slug,
        "label": label,
        "fields": fields,
        "checked_paths": checked,
    }


def build_view_field_sections(
    element_stereotypes: list[str],
    relationship_stereotypes: list[str],
    selected_fields: dict[str, list[str]] | None = None,
    stereotype_fields: dict[str, list[dict[str, str]]] | None = None,
) -> list[dict[str, Any]]:
    """Build stereotype-grouped field checklists for the Filters panel."""
    selected_fields = selected_fields or {}
    catalog = stereotype_fields or {}
    logger.info(
        "browse_content.build_view_field_sections | processing | element_count=%s "
        "relationship_count=%s catalog_count=%s",
        len(element_stereotypes),
        len(relationship_stereotypes),
        len(catalog),
    )

    def _fields_for(slug: str, *, is_edge: bool) -> list[dict[str, str]]:
        if slug in catalog:
            return catalog[slug]
        fallback = STEREOTYPE_FIELD_SCHEMA.get(slug)
        if fallback:
            return fallback
        return (
            [{"path": "stereotype", "label": "Stereotype"}]
            if is_edge
            else [{"path": "name", "label": "Name"}]
        )

    element_sections = [
        _field_section(
            kind="element",
            slug=slug,
            fields=_fields_for(slug, is_edge=False),
            selected_fields=selected_fields,
        )
        for slug in element_stereotypes
    ]
    relationship_sections = [
        _field_section(
            kind="relationship",
            slug=slug,
            fields=_fields_for(slug, is_edge=True),
            selected_fields=selected_fields,
        )
        for slug in relationship_stereotypes
    ]
    sections = element_sections + relationship_sections
    logger.info(
        "browse_content.build_view_field_sections | exit | section_count=%s",
        len(sections),
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
