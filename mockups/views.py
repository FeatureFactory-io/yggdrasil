import json
import logging
import re
from typing import Any
from urllib.parse import urlencode

from django.shortcuts import render

from yggdrasil.web.browse_helpers import build_package_tree as _build_package_tree

logger = logging.getLogger(__name__)

MOCK_MODEL_SLUG = "yggdrasil"
MOCK_MAX_DEPTH = 5
MOCK_DEFAULT_MODE = "graph"
MOCK_DEFAULT_DEPTH = 2

HEALTH_FILTER_MAP = {
    "ok": "green",
    "warning": "yellow",
    "error": "red",
    "green": "green",
    "yellow": "yellow",
    "red": "red",
}

# ─── Confidence banding — IA_guidelines.md §15.6 ─────────────────────────────
# Bands: >=0.85 high, 0.60-0.84 medium, 0.40-0.59 low, <0.40 vlow.
# Each mock element/relationship gets `conf_pct` (int, for CSS width) and
# `conf_band` (str, for the var(--yrg-conf-{band}) fill color) so templates
# never need to compute a percentage or pick a color themselves.

CONFIDENCE_BAND_THRESHOLDS = (
    (0.85, "high"),
    (0.60, "medium"),
    (0.40, "low"),
)


def confidence_band(confidence: float) -> str:
    """Map a 0.0-1.0 confidence score to its §15.6 semantic band.

    :param confidence: Confidence score in the closed interval [0.0, 1.0].
    :return: One of "high", "medium", "low", "vlow".
    """
    for threshold, band in CONFIDENCE_BAND_THRESHOLDS:
        if confidence >= threshold:
            return band
    return "vlow"


def annotate_confidence(items: list[dict]) -> list[dict]:
    """Attach `conf_pct` and `conf_band` to each dict's `confidence` value.

    :param items: Mock element or relationship dicts, each with a
        `confidence` key holding a 0.0-1.0 float.
    :return: The same list, mutated in place, for convenient chaining.
    """
    for item in items:
        item["conf_pct"] = round(item["confidence"] * 100)
        item["conf_band"] = confidence_band(item["confidence"])
    return items


# ─── Mock data ───────────────────────────────────────────────────────────────

MOCK_ELEMENTS = [
    {
        "id": 1,
        "name": "Payment API",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "payments-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.92,
        "properties": {"version": "2.3.1", "language": "Python", "framework": "FastAPI"},
        "relationships_in": 4,
        "relationships_out": 6,
        "last_verified": "2026-07-10",
    },
    {
        "id": 2,
        "name": "Notification Service",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "platform-team",
        "health": "yellow",
        "source": "human",
        "confidence": 1.0,
        "properties": {"version": "1.0.0", "language": "Python", "framework": "Celery"},
        "relationships_in": 2,
        "relationships_out": 3,
        "last_verified": "2026-07-14",
    },
    {
        "id": 3,
        "name": "Order Domain",
        "stereotype": "Component",
        "package": "Application",
        "owner": "fulfillment-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.87,
        "properties": {"version": "3.1.0", "language": "Python"},
        "relationships_in": 8,
        "relationships_out": 4,
        "last_verified": "2026-07-10",
    },
    {
        "id": 4,
        "name": "Fulfillment Worker",
        "stereotype": "Component",
        "package": "Application",
        "owner": "fulfillment-team",
        "health": "red",
        "source": "ratatosk",
        "confidence": 0.71,
        "properties": {"version": "2.0.0", "language": "Python"},
        "relationships_in": 2,
        "relationships_out": 5,
        "last_verified": "2026-07-10",
    },
    {
        "id": 5,
        "name": "PostgreSQL",
        "stereotype": "System",
        "package": "Technology",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.99,
        "properties": {"version": "15.2"},
        "relationships_in": 7,
        "relationships_out": 0,
        "last_verified": "2026-07-10",
    },
    {
        "id": 6,
        "name": "Mobile App",
        "stereotype": "System",
        "package": "Context",
        "owner": "mobile-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"platform": "iOS + Android"},
        "relationships_in": 0,
        "relationships_out": 3,
        "last_verified": "2026-07-10",
    },
]

MOCK_RELATIONSHIPS = [
    {
        "id": 1,
        "from_element": "Mobile App",
        "from_id": 6,
        "edge_stereotype": "calls",
        "to_element": "Payment API",
        "to_id": 1,
        "confidence": 0.95,
        "source": "ratatosk",
        "properties": {"protocol": "HTTPS", "async": False},
    },
    {
        "id": 2,
        "from_element": "Payment API",
        "from_id": 1,
        "edge_stereotype": "depends_on",
        "to_element": "PostgreSQL",
        "to_id": 5,
        "confidence": 0.99,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 3,
        "from_element": "Payment API",
        "from_id": 1,
        "edge_stereotype": "calls",
        "to_element": "Notification Service",
        "to_id": 2,
        "confidence": 0.92,
        "source": "ratatosk",
        "properties": {"protocol": "AMQP", "async": True},
    },
    {
        "id": 4,
        "from_element": "Order Domain",
        "from_id": 3,
        "edge_stereotype": "depends_on",
        "to_element": "Payment API",
        "to_id": 1,
        "confidence": 0.87,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 5,
        "from_element": "Fulfillment Worker",
        "from_id": 4,
        "edge_stereotype": "reads_from",
        "to_element": "PostgreSQL",
        "to_id": 5,
        "confidence": 0.71,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 6,
        "from_element": "Order Domain",
        "from_id": 3,
        "edge_stereotype": "serves",
        "to_element": "Fulfillment Worker",
        "to_id": 4,
        "confidence": 0.85,
        "source": "ratatosk",
        "properties": {},
    },
]

annotate_confidence(MOCK_ELEMENTS)
annotate_confidence(MOCK_RELATIONSHIPS)

# ─── View Browser mock — Yggdrasil self-model (Ratatosk bootstrap snapshot) ──
# Mirrors live graph: Context / Application / Technology packages with Django apps
# as Components. Used only by VIEW-BROWSE-1 mockup (three-panel explorer).

MOCK_VIEW_BROWSER_ELEMENTS = [
    {
        "id": 283,
        "name": "Yggdrasil",
        "slug": "yggdrasil",
        "stereotype": "System",
        "package": "Context",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"description": "AI-augmented architecture knowledge graph"},
        "relationships_in": 0,
        "relationships_out": 0,
        "last_verified": "2026-07-14",
    },
    {
        "id": 280,
        "name": "Browser (HTMX)",
        "slug": "browser-htmx",
        "stereotype": "Person",
        "package": "Context",
        "owner": "",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {},
        "relationships_in": 0,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 281,
        "name": "AI agents",
        "slug": "ai-agents",
        "stereotype": "Person",
        "package": "Context",
        "owner": "",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.8,
        "properties": {},
        "relationships_in": 0,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 282,
        "name": "Backend (web + Celery)",
        "slug": "backend-web-celery",
        "stereotype": "Container",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"runtime": "Django 5.1 + Celery 5"},
        "relationships_in": 12,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 285,
        "name": "MCP facade",
        "slug": "mcp-facade",
        "stereotype": "Container",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"image": "ghcr.io/yggdrasil/yggdrasil-mcp"},
        "relationships_in": 2,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 284,
        "name": "Ratatosk CLI",
        "slug": "ratatosk-cli",
        "stereotype": "Container",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"distribution": "PyPI"},
        "relationships_in": 0,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 286,
        "name": "Worker",
        "slug": "worker",
        "stereotype": "Container",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {},
        "relationships_in": 0,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 290,
        "name": "auth",
        "slug": "auth",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.auth"},
        "relationships_in": 2,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 291,
        "name": "graph",
        "slug": "graph",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.graph"},
        "relationships_in": 4,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 292,
        "name": "changeset",
        "slug": "changeset",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.changeset"},
        "relationships_in": 3,
        "relationships_out": 2,
        "last_verified": "2026-07-14",
    },
    {
        "id": 293,
        "name": "munin",
        "slug": "munin",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.munin", "jira_key": "YGG-142", "version": "0.4.2"},
        "relationships_in": 0,
        "relationships_out": 2,
        "last_verified": "2026-07-14",
    },
    {
        "id": 294,
        "name": "ratatosk",
        "slug": "ratatosk",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.ratatosk"},
        "relationships_in": 0,
        "relationships_out": 2,
        "last_verified": "2026-07-14",
    },
    {
        "id": 295,
        "name": "mcp",
        "slug": "mcp",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.mcp"},
        "relationships_in": 1,
        "relationships_out": 1,
        "last_verified": "2026-07-14",
    },
    {
        "id": 296,
        "name": "api",
        "slug": "api",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.api"},
        "relationships_in": 0,
        "relationships_out": 5,
        "last_verified": "2026-07-14",
    },
    {
        "id": 297,
        "name": "web",
        "slug": "web",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"app": "yggdrasil.web", "jira_key": "YGG-88"},
        "relationships_in": 0,
        "relationships_out": 4,
        "last_verified": "2026-07-14",
    },
    {
        "id": 298,
        "name": "llm",
        "slug": "llm",
        "stereotype": "Component",
        "package": "Application",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.85,
        "properties": {"app": "yggdrasil.llm"},
        "relationships_in": 2,
        "relationships_out": 2,
        "last_verified": "2026-07-14",
    },
    {
        "id": 287,
        "name": "PostgreSQL",
        "slug": "postgre-sql",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"version": "16"},
        "relationships_in": 0,
        "relationships_out": 0,
        "last_verified": "2026-07-14",
    },
    {
        "id": 288,
        "name": "Redis",
        "slug": "redis",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.95,
        "properties": {"version": "7"},
        "relationships_in": 2,
        "relationships_out": 0,
        "last_verified": "2026-07-14",
    },
    {
        "id": 289,
        "name": "Ollama",
        "slug": "ollama",
        "stereotype": "Container",
        "package": "Technology",
        "owner": "platform-team",
        "health": "green",
        "source": "ratatosk",
        "confidence": 0.9,
        "properties": {"mode": "local LLM"},
        "relationships_in": 1,
        "relationships_out": 0,
        "last_verified": "2026-07-14",
    },
]

MOCK_VIEW_BROWSER_RELATIONSHIPS = [
    {
        "id": 194,
        "from_id": 280,
        "to_id": 282,
        "from_element": "Browser (HTMX)",
        "to_element": "Backend (web + Celery)",
        "edge_stereotype": "uses",
        "confidence": 0.9,
        "source": "ratatosk",
        "properties": {"protocol": "HTTPS"},
    },
    {
        "id": 217,
        "from_id": 285,
        "to_id": 282,
        "from_element": "MCP facade",
        "to_element": "Backend (web + Celery)",
        "edge_stereotype": "calls",
        "confidence": 0.95,
        "source": "ratatosk",
        "properties": {"protocol": "HTTP"},
    },
    {
        "id": 218,
        "from_id": 284,
        "to_id": 285,
        "from_element": "Ratatosk CLI",
        "to_element": "MCP facade",
        "edge_stereotype": "calls",
        "confidence": 0.9,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 219,
        "from_id": 281,
        "to_id": 285,
        "from_element": "AI agents",
        "to_element": "MCP facade",
        "edge_stereotype": "uses",
        "confidence": 0.85,
        "source": "ratatosk",
        "properties": {"via": "MCP"},
    },
    {
        "id": 197,
        "from_id": 290,
        "to_id": 282,
        "from_element": "auth",
        "to_element": "Backend (web + Celery)",
        "edge_stereotype": "depends_on",
        "confidence": 0.9,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 199,
        "from_id": 291,
        "to_id": 282,
        "from_element": "graph",
        "to_element": "Backend (web + Celery)",
        "edge_stereotype": "depends_on",
        "confidence": 0.9,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 202,
        "from_id": 293,
        "to_id": 282,
        "from_element": "munin",
        "to_element": "Backend (web + Celery)",
        "edge_stereotype": "depends_on",
        "confidence": 0.9,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 214,
        "from_id": 293,
        "to_id": 298,
        "from_element": "munin",
        "to_element": "llm",
        "edge_stereotype": "depends_on",
        "confidence": 0.88,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 211,
        "from_id": 292,
        "to_id": 291,
        "from_element": "changeset",
        "to_element": "graph",
        "edge_stereotype": "depends_on",
        "confidence": 0.92,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 204,
        "from_id": 282,
        "to_id": 288,
        "from_element": "Backend (web + Celery)",
        "to_element": "Redis",
        "edge_stereotype": "depends_on",
        "confidence": 0.95,
        "source": "ratatosk",
        "properties": {},
    },
    {
        "id": 206,
        "from_id": 298,
        "to_id": 289,
        "from_element": "llm",
        "to_element": "Ollama",
        "edge_stereotype": "depends_on",
        "confidence": 0.85,
        "source": "ratatosk",
        "properties": {},
    },
]

annotate_confidence(MOCK_VIEW_BROWSER_ELEMENTS)
annotate_confidence(MOCK_VIEW_BROWSER_RELATIONSHIPS)

# Named Views (Views v1 prototype) — persisted snapshots per Model + owner in W14.
MOCK_BROWSE_VIEWS: list[dict[str, Any]] = [
    {
        "name": "Application / Components",
        "slug": "application-components",
        "model_slug": MOCK_MODEL_SLUG,
        "payload": {
            "filters": {
                "packages": ["application"],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 2},
            "presentation": "graph",
            "content": {
                "field_map": {
                    "component": ["name", "owner", "health"],
                }
            },
        },
    },
    {
        "name": "Technology / Infrastructure",
        "slug": "technology-infrastructure",
        "model_slug": MOCK_MODEL_SLUG,
        "payload": {
            "filters": {
                "packages": ["technology"],
                "element_stereotypes": [],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 3},
            "presentation": "graph",
        },
    },
    {
        "name": "Payment capability review",
        "slug": "payment-capability-review",
        "model_slug": MOCK_MODEL_SLUG,
        "payload": {
            "filters": {
                "packages": [],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": ["depends_on"],
            },
            "levels": {"depth": 2},
            "presentation": "graph",
            "content": {
                "field_map": {
                    "component": ["name", "owner", "properties.jira_key"],
                    "depends_on": ["stereotype", "properties.protocol"],
                }
            },
        },
    },
]


MOCK_DEFAULT_CONTENT_PRESET = "current-state"
MOCK_CONTENT_CUSTOM_SLUG = "custom"

MOCK_CONTENT_FIELDS: list[dict[str, str]] = [
    {"path": "name", "label": "Name"},
    {"path": "stereotype", "label": "Stereotype"},
    {"path": "owner", "label": "Owner"},
    {"path": "health", "label": "Health"},
    {"path": "package", "label": "Package"},
    {"path": "properties.jira_key", "label": "Jira key"},
    {"path": "properties.version", "label": "Version"},
    {"path": "source", "label": "Source"},
]

MOCK_CONTENT_PRESETS: dict[str, dict[str, Any]] = {
    "minimal": {
        "slug": "minimal",
        "name": "Minimal",
        "table_columns": ["name", "stereotype", "package"],
        "node_bindings": {"primary": "name", "secondary": []},
        "edge_label": "stereotype",
    },
    "current-state": {
        "slug": "current-state",
        "name": "Current State",
        "table_columns": ["name", "stereotype", "owner", "health", "package"],
        "node_bindings": {"primary": "name", "secondary": ["owner", "health"]},
        "edge_label": "stereotype",
    },
    "jira-info": {
        "slug": "jira-info",
        "name": "Jira Info",
        "table_columns": ["name", "stereotype", "owner", "properties.jira_key"],
        "node_bindings": {"primary": "name", "secondary": ["properties.jira_key", "owner"]},
        "edge_label": "stereotype",
    },
    MOCK_CONTENT_CUSTOM_SLUG: {
        "slug": MOCK_CONTENT_CUSTOM_SLUG,
        "name": "Custom",
        "table_columns": ["name", "stereotype", "package"],
        "node_bindings": {"primary": "name", "secondary": []},
        "edge_label": "stereotype",
    },
}

TABLE_COLUMN_LABELS: dict[str, str] = {
    field["path"]: field["label"] for field in MOCK_CONTENT_FIELDS
}


def field_path_label(path: str) -> str:
    """Human-readable label for a Content field path.

    :param path: Element field path, e.g. ``owner`` or ``properties.jira_key``.
    :return: Display label for graph ``key: value`` lines.
    """
    if path in TABLE_COLUMN_LABELS:
        return TABLE_COLUMN_LABELS[path]
    if path.startswith("properties."):
        prop = path.split(".", 1)[1]
        return prop.replace("_", " ").title()
    return path.replace("_", " ").title()


def format_mock_node_label_from_paths(element: dict[str, Any], field_paths: list[str]) -> str:
    """Build in-node graph label lines as ``Key: value`` for each visible field.

    :param element: Mock element dict.
    :param field_paths: Ordered field paths from the active View ``field_map``.
    :return: Newline-separated label text rendered inside the node shape.
    """
    lines: list[str] = []
    for path in field_paths:
        value = _element_field_value(element, path)
        if not value:
            continue
        lines.append(f"{field_path_label(path)}: {value}")
    if lines:
        return "\n".join(lines)
    name = _element_field_value(element, "name") or "—"
    return f"{field_path_label('name')}: {name}"


def preset_to_content_block(slug: str) -> dict[str, Any]:
    """Build a v2 ``content`` payload block from a built-in preset slug.

    :param slug: Built-in preset slug.
    :return: Content block with ``preset`` and ``bindings`` keys.
    """
    preset = resolve_content_preset(slug)
    return {
        "preset": preset["slug"],
        "bindings": {
            "nodes": {"*": dict(preset["node_bindings"])},
            "edges": {"*": {"label": preset["edge_label"]}},
            "table": list(preset["table_columns"]),
        },
    }


def bindings_to_display_config(content_block: dict[str, Any]) -> dict[str, Any]:
    """Flatten a v2 content block into template/JS display config.

    :param content_block: ``content`` object from BrowseView payload or editor.
    :return: Dict with slug, name, node_bindings, edge_label, table_columns.
    """
    bindings = content_block.get("bindings") or {}
    node = bindings.get("nodes", {}).get("*", {"primary": "name", "secondary": []})
    edge = bindings.get("edges", {}).get("*", {"label": "stereotype"})
    table = list(bindings.get("table") or ["name", "stereotype", "package"])
    preset_slug = content_block.get("preset") or MOCK_DEFAULT_CONTENT_PRESET
    preset_meta = MOCK_CONTENT_PRESETS.get(preset_slug, MOCK_CONTENT_PRESETS["minimal"])
    name = preset_meta["name"]
    if preset_slug == MOCK_CONTENT_CUSTOM_SLUG:
        name = "Custom"
    return {
        "slug": preset_slug,
        "name": name,
        "node_bindings": {
            "primary": node.get("primary", "name"),
            "secondary": list(node.get("secondary") or []),
        },
        "edge_label": edge.get("label", "stereotype"),
        "table_columns": table,
    }


def resolve_effective_content(
    params: dict[str, Any], saved_content: dict[str, Any] | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Resolve display config and canonical content block for the active browse state.

    :param params: Parsed browse params.
    :param saved_content: ``content`` from a named View payload when ``browse_view`` is set.
    :return: Tuple of (display_config, content_block).
    """
    if saved_content and saved_content.get("bindings"):
        block = saved_content
        return bindings_to_display_config(block), block

    slug = params.get("content") or MOCK_DEFAULT_CONTENT_PRESET
    if slug == MOCK_CONTENT_CUSTOM_SLUG:
        block = preset_to_content_block(MOCK_DEFAULT_CONTENT_PRESET)
        block["preset"] = MOCK_CONTENT_CUSTOM_SLUG
        display = bindings_to_display_config(block)
        return display, block

    block = preset_to_content_block(slug)
    return bindings_to_display_config(block), block


def resolve_content_preset(slug: str | None) -> dict[str, Any]:
    """Return built-in Content preset config; fall back to minimal on unknown slug.

    :param slug: Preset slug from ``?content=`` or saved View payload.
    :return: Preset dict with bindings for graph labels and table columns.
    """
    key = (slug or "").strip() or MOCK_DEFAULT_CONTENT_PRESET
    if key == MOCK_CONTENT_CUSTOM_SLUG:
        return MOCK_CONTENT_PRESETS[MOCK_CONTENT_CUSTOM_SLUG]
    if key not in MOCK_CONTENT_PRESETS:
        logger.warning("Mockup: unknown content preset=%s, using minimal", key)
        key = "minimal"
    return MOCK_CONTENT_PRESETS[key]


def _element_field_value(element: dict[str, Any], path: str) -> str:
    """Resolve a dot-path field on a mock element (e.g. ``properties.jira_key``).

    :param element: Mock element dict.
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
    if path.startswith("properties."):
        prop_key = path.split(".", 1)[1]
        return str(element.get("properties", {}).get(prop_key, ""))
    return str(element.get(path, ""))


def _relationship_field_value(relationship: dict[str, Any], path: str) -> str:
    """Resolve a field path on a mock relationship.

    :param relationship: Mock relationship dict.
    :param path: Field path (``stereotype``, ``properties.*``, etc.).
    :return: Display string or empty when missing.
    """
    if path == "stereotype":
        return str(relationship.get("edge_stereotype", ""))
    if path.startswith("properties."):
        prop_key = path.split(".", 1)[1]
        return str(relationship.get("properties", {}).get(prop_key, ""))
    return str(relationship.get(path, ""))


def field_map_to_content_display(
    field_map: dict[str, list[str]],
    element_stereotypes: list[str],
    relationship_stereotypes: list[str],
) -> dict[str, Any]:
    """Convert v2 ``field_map`` into graph/table display bindings.

    :param field_map: Stereotype slug → checked field paths from the Filters panel.
    :param element_stereotypes: Active element stereotype slugs.
    :param relationship_stereotypes: Active relationship stereotype slugs.
    :return: Dict with ``nodes``, ``edges``, and ``table_columns`` bindings.
    """
    nodes: dict[str, dict[str, Any]] = {}
    for slug in element_stereotypes:
        paths = list(field_map.get(slug) or [])
        if not paths:
            schema = MOCK_STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "name"}])
            paths = [row["path"] for row in schema]
        nodes[slug] = {"primary": paths[0], "secondary": paths[1:]}

    edges: dict[str, dict[str, Any]] = {}
    for slug in relationship_stereotypes:
        paths = list(field_map.get(slug) or [])
        if not paths:
            schema = MOCK_STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "stereotype"}])
            paths = [row["path"] for row in schema]
        edges[slug] = {"fields": paths}

    table_columns = build_table_columns_from_params(
        {
            "field_map": field_map,
            "element_stereotypes": element_stereotypes,
        }
    )
    return {
        "nodes": nodes,
        "edges": edges,
        "table_columns": [col["key"] for col in table_columns],
    }


def format_mock_node_label_for_element(
    element: dict[str, Any], content_display: dict[str, Any]
) -> str:
    """Format a graph node label using stereotype-specific Content bindings.

    :param element: Mock element dict.
    :param content_display: Output of :func:`field_map_to_content_display`.
    :return: Multi-line Cytoscape label text.
    """
    slug = _stereotype_slug(element.get("stereotype", ""))
    bindings = content_display.get("nodes", {}).get(slug, {"primary": "name", "secondary": []})
    paths = [bindings.get("primary", "name"), *list(bindings.get("secondary") or [])]
    return format_mock_node_label_from_paths(element, paths)


def format_mock_edge_label_for_relationship(
    relationship: dict[str, Any], content_display: dict[str, Any]
) -> str:
    """Format a graph edge label from relationship stereotype field bindings.

    :param relationship: Mock relationship dict.
    :param content_display: Output of :func:`field_map_to_content_display`.
    :return: Single-line edge label for Cytoscape.
    """
    slug = _stereotype_slug(relationship.get("edge_stereotype", ""))
    fields = content_display.get("edges", {}).get(slug, {}).get("fields", ["stereotype"])
    parts: list[str] = []
    for path in fields:
        value = _relationship_field_value(relationship, path)
        if not value:
            continue
        if path == "stereotype":
            parts.append(value)
        elif path.startswith("properties."):
            parts.append(f"{path.split('.', 1)[1]}: {value}")
        else:
            parts.append(value)
    if parts:
        return " · ".join(parts)
    return str(relationship.get("edge_stereotype", ""))


def _parse_field_map_from_request(request) -> dict[str, list[str]]:
    """Parse ``field_{stereotype}`` repeated query params into a field map.

    :param request: HTTP request with optional ``field_component=name`` params.
    :return: Stereotype slug → list of field paths.
    """
    field_map: dict[str, list[str]] = {}
    for key in request.GET:
        if not key.startswith("field_"):
            continue
        slug = key[6:].lower()
        if not slug:
            continue
        for raw in request.GET.getlist(key):
            val = str(raw).strip()
            if val:
                field_map.setdefault(slug, []).append(val)
    return field_map


def enrich_mock_canvas_rows(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    table_columns: list[dict[str, str]],
    content_display: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach rendered labels and table cell values for canvas display.

    :param elements: Filtered mock elements.
    :param relationships: Relationships touching visible elements.
    :param table_columns: Active table column metadata.
    :param content_display: Content bindings from :func:`field_map_to_content_display`.
    :return: Tuple of enriched element and relationship row dicts.
    """
    display_elements: list[dict[str, Any]] = []
    for element in elements:
        row = dict(element)
        row["node_label"] = format_mock_node_label_for_element(element, content_display)
        row["table_cells"] = [
            {
                "key": col["key"],
                "value": table_cell_display(element, col["key"]),
            }
            for col in table_columns
        ]
        display_elements.append(row)

    display_relationships: list[dict[str, Any]] = []
    for relationship in relationships:
        row = dict(relationship)
        row["edge_label"] = format_mock_edge_label_for_relationship(relationship, content_display)
        display_relationships.append(row)
    return display_elements, display_relationships


def format_mock_node_label(element: dict[str, Any], display: dict[str, Any]) -> str:
    """Format Cytoscape node label from Content display config.

    :param element: Mock element dict.
    :param display: Display config from :func:`bindings_to_display_config`.
    :return: In-node ``Key: value`` lines joined by newline.
    """
    bindings = display.get("node_bindings", {})
    paths = [bindings.get("primary", "name"), *list(bindings.get("secondary") or [])]
    return format_mock_node_label_from_paths(element, paths)


def build_mock_table_columns(display: dict[str, Any]) -> list[dict[str, str]]:
    """Build table header metadata for the active Content display config.

    :param display: Display config from :func:`bindings_to_display_config`.
    :return: Column descriptors with ``key`` and ``label``.
    """
    return [
        {"key": key, "label": TABLE_COLUMN_LABELS.get(key, key.replace("_", " ").title())}
        for key in display.get("table_columns", [])
    ]


def table_cell_display(element: dict[str, Any], column_key: str) -> str:
    """Resolve a table cell value for a Content column path.

    :param element: Mock element dict.
    :param column_key: Field path from content bindings table list.
    :return: Display string or em dash when empty.
    """
    value = _element_field_value(element, column_key)
    return value if value else "—"


def build_content_preset_links(path: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """Build dropdown URLs preserving active browse state except Content slug.

    :param path: Mock browse base path.
    :param params: Parsed browse params.
    :return: Preset link rows for template rendering.
    """
    current = params.get("content") or MOCK_DEFAULT_CONTENT_PRESET
    links: list[dict[str, Any]] = []
    for preset in MOCK_CONTENT_PRESETS.values():
        if preset["slug"] == MOCK_CONTENT_CUSTOM_SLUG:
            continue
        query: dict[str, str] = {
            "mode": str(params.get("mode") or MOCK_DEFAULT_MODE),
            "depth": str(params.get("depth") or MOCK_DEFAULT_DEPTH),
            "content": preset["slug"],
        }
        for key in ("package", "stereotype", "health", "as_of", "browse_view"):
            if params.get(key):
                query[key] = str(params[key])
        links.append(
            {
                "slug": preset["slug"],
                "name": preset["name"],
                "url": f"{path}?{urlencode(query)}",
                "active": preset["slug"] == current and current != MOCK_CONTENT_CUSTOM_SLUG,
            }
        )
    return links


MOCK_ELEMENT_STEREOTYPE_OPTIONS: list[dict[str, str]] = [
    {"slug": "system", "name": "System"},
    {"slug": "container", "name": "Container"},
    {"slug": "component", "name": "Component"},
    {"slug": "person", "name": "Person"},
]

MOCK_RELATIONSHIP_STEREOTYPE_OPTIONS: list[dict[str, str]] = [
    {"slug": "depends_on", "name": "depends_on"},
    {"slug": "calls", "name": "calls"},
    {"slug": "reads_from", "name": "reads_from"},
]

MOCK_STEREOTYPE_FIELD_SCHEMA: dict[str, list[dict[str, str]]] = {
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
        {"path": "properties.async", "label": "Async"},
    ],
    "reads_from": [
        {"path": "stereotype", "label": "Stereotype"},
    ],
}


def _get_query_list(request, key: str) -> list[str]:
    """Return deduplicated non-empty values from repeated query params.

    :param request: HTTP request.
    :param key: Query param name.
    :return: Normalized slug list.
    """
    seen: set[str] = set()
    values: list[str] = []
    for raw in request.GET.getlist(key):
        val = str(raw).strip().lower()
        if val and val not in seen:
            seen.add(val)
            values.append(val)
    return values


def _normalize_view_filters(filters: dict[str, Any]) -> dict[str, list[str]]:
    """Coerce legacy single-value filter keys to v2 list shape.

    :param filters: Raw filters dict from a View payload or query string.
    :return: Dict with ``packages``, ``element_stereotypes``, ``relationship_stereotypes``.
    """
    packages = filters.get("packages")
    if not packages:
        single = filters.get("package") or ""
        packages = [single] if single else []
    element_stereotypes = filters.get("element_stereotypes")
    if not element_stereotypes:
        single = filters.get("stereotype") or ""
        element_stereotypes = [single] if single else []
    relationship_stereotypes = filters.get("relationship_stereotypes") or []
    return {
        "packages": [str(p).lower() for p in packages if p],
        "element_stereotypes": [str(s).lower() for s in element_stereotypes if s],
        "relationship_stereotypes": [str(s).lower() for s in relationship_stereotypes if s],
    }


def build_view_field_sections(
    element_stereotypes: list[str],
    relationship_stereotypes: list[str],
    selected_fields: dict[str, list[str]] | None = None,
) -> list[dict[str, Any]]:
    """Build stereotype-grouped field checklists for the active View.

    :param element_stereotypes: Selected element stereotype slugs.
    :param relationship_stereotypes: Selected relationship stereotype slugs.
    :param selected_fields: Map stereotype slug → checked field paths; defaults all on.
    :return: Section dicts for template rendering.
    """
    selected_fields = selected_fields or {}
    sections: list[dict[str, Any]] = []
    for slug in element_stereotypes:
        fields = MOCK_STEREOTYPE_FIELD_SCHEMA.get(slug, [{"path": "name", "label": "Name"}])
        checked = selected_fields.get(slug) or [f["path"] for f in fields]
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
        fields = MOCK_STEREOTYPE_FIELD_SCHEMA.get(
            slug, [{"path": "stereotype", "label": "Stereotype"}]
        )
        checked = selected_fields.get(slug) or [f["path"] for f in fields]
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


def slugify_view_name(name: str) -> str:
    """Derive a URL-safe slug from a display name.

    :param name: Human-readable View label.
    :return: Lowercase hyphenated slug.
    """
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"[\s_]+", "-", slug.strip())
    return slug[:64] or "view"


def _blank_to_none(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _find_browse_view(slug: str, model_slug: str) -> dict[str, Any] | None:
    for view in MOCK_BROWSE_VIEWS:
        if view["slug"] == slug and view["model_slug"] == model_slug:
            return view
    return None


def parse_mock_browse_params(request, model_slug: str = MOCK_MODEL_SLUG) -> dict[str, Any]:
    """Parse mock View Browser query params; expand ``browse_view`` when present.

    :param request: Incoming HTTP request.
    :param model_slug: Active Model slug for View catalog scoping.
    :return: Normalized browse state dict for template + filtering.
    """
    browse_view_slug = _blank_to_none(request.GET.get("browse_view"))
    if browse_view_slug:
        saved = _find_browse_view(browse_view_slug, model_slug)
        if saved:
            payload = saved["payload"]
            filters = _normalize_view_filters(payload.get("filters", {}))
            field_map = (payload.get("content") or {}).get("field_map") or {}
            query_field_map = _parse_field_map_from_request(request)
            if query_field_map:
                field_map = query_field_map
            return {
                "packages": filters["packages"],
                "element_stereotypes": filters["element_stereotypes"],
                "relationship_stereotypes": filters["relationship_stereotypes"],
                "depth": int(payload.get("levels", {}).get("depth", MOCK_DEFAULT_DEPTH)),
                "mode": payload.get("presentation", MOCK_DEFAULT_MODE),
                "browse_view": browse_view_slug,
                "loaded_view_name": saved["name"],
                "field_map": field_map,
                "viewport": payload.get("viewport"),
                "baseline_browse_view": browse_view_slug,
            }
        logger.warning(
            "Mockup: unknown browse_view slug=%s model=%s",
            browse_view_slug,
            model_slug,
        )

    mode = request.GET.get("mode") or request.GET.get("view") or MOCK_DEFAULT_MODE
    if mode not in ("graph", "table"):
        mode = MOCK_DEFAULT_MODE

    try:
        depth = int(request.GET.get("depth", MOCK_DEFAULT_DEPTH))
    except (TypeError, ValueError):
        depth = MOCK_DEFAULT_DEPTH
    depth = max(1, min(depth, MOCK_MAX_DEPTH))

    packages = _get_query_list(request, "package")
    element_stereotypes = _get_query_list(request, "stereotype")
    relationship_stereotypes = _get_query_list(request, "edge_stereotype")
    field_map = _parse_field_map_from_request(request)

    return {
        "packages": packages,
        "element_stereotypes": element_stereotypes,
        "relationship_stereotypes": relationship_stereotypes,
        "depth": depth,
        "mode": mode,
        "browse_view": "",
        "loaded_view_name": "",
        "field_map": field_map,
        "viewport": None,
        "baseline_browse_view": "",
    }


def filter_mock_elements(elements: list[dict], params: dict[str, Any]) -> list[dict]:
    """Apply mock browse filters to the element list.

    :param elements: Full mock element catalog.
    :param params: Parsed browse params from :func:`parse_mock_browse_params`.
    :return: Filtered element list (client graph uses same subset).
    """
    filtered = list(elements)

    packages = params.get("packages") or []
    if packages:
        pkg_set = {p.lower() for p in packages}
        filtered = [
            el
            for el in filtered
            if el.get("package", "").lower() in pkg_set
            or el.get("package_slug", "").lower() in pkg_set
        ]

    stereotypes = params.get("element_stereotypes") or []
    if stereotypes:
        st_set = {s.lower() for s in stereotypes}
        filtered = [el for el in filtered if el.get("stereotype", "").lower() in st_set]

    return filtered


def _element_package_slug(element: dict) -> str:
    """Return normalized package slug for a mock element.

    :param element: Mock element dict.
    :return: Lowercase package slug, e.g. ``application``.
    """
    return (element.get("package_slug") or element.get("package") or "").lower()


def _stereotype_slug(name: str) -> str:
    """Normalize stereotype display name to filter slug.

    :param name: Stereotype label from mock data.
    :return: Lowercase slug, e.g. ``depends_on``.
    """
    return str(name or "").strip().lower().replace(" ", "_")


def build_package_scoped_filter_options(
    elements: list[dict],
    relationships: list[dict],
    packages: list[str] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """Build element/relationship stereotype options scoped to selected packages.

    When no packages are selected, all stereotypes present in the mock catalog
    are returned. When packages are selected, only stereotypes that appear on
    elements (or relationships touching those elements) within the scope remain.

    :param elements: Full mock element catalog.
    :param relationships: Full mock relationship catalog.
    :param packages: Selected package slugs, or empty for full catalog.
    :return: Dict with ``stereotypes`` and ``relationship_stereotypes`` lists.
    """
    pkg_filter = {p.lower() for p in packages} if packages else None
    scoped_elements = (
        [el for el in elements if _element_package_slug(el) in pkg_filter]
        if pkg_filter
        else list(elements)
    )
    element_ids = {el["id"] for el in scoped_elements}

    element_st_map: dict[str, str] = {}
    for el in scoped_elements:
        slug = _stereotype_slug(el.get("stereotype", ""))
        if slug:
            element_st_map[slug] = str(el.get("stereotype", slug))

    rel_st_map: dict[str, str] = {}
    for rel in relationships:
        if not pkg_filter or rel["from_id"] in element_ids or rel["to_id"] in element_ids:
            slug = _stereotype_slug(rel.get("edge_stereotype", ""))
            if slug:
                rel_st_map[slug] = str(rel.get("edge_stereotype", slug))

    def _sorted_options(st_map: dict[str, str]) -> list[dict[str, str]]:
        return [{"slug": slug, "name": st_map[slug]} for slug in sorted(st_map)]

    return {
        "stereotypes": _sorted_options(element_st_map),
        "relationship_stereotypes": _sorted_options(rel_st_map),
    }


def build_filter_catalog_payload(
    elements: list[dict], relationships: list[dict]
) -> dict[str, list[dict[str, str | int]]]:
    """Compact catalog for client-side filter panel cascading.

    :param elements: Full mock element catalog.
    :param relationships: Full mock relationship catalog.
    :return: JSON-serializable payload for ``mock-filter-catalog`` script tag.
    """
    return {
        "elements": [
            {
                "id": el["id"],
                "package": _element_package_slug(el),
                "stereotype": _stereotype_slug(el.get("stereotype", "")),
            }
            for el in elements
        ],
        "relationships": [
            {
                "from_id": rel["from_id"],
                "to_id": rel["to_id"],
                "edge_stereotype": _stereotype_slug(rel.get("edge_stereotype", "")),
            }
            for rel in relationships
        ],
    }


def build_mock_filter_options(elements: list[dict]) -> dict[str, list[dict[str, str]]]:
    """Build filter dropdown options from mock elements."""
    packages: dict[str, str] = {}
    stereotypes: dict[str, str] = {}
    for el in elements:
        pkg = el.get("package", "")
        if pkg:
            packages[pkg.lower()] = pkg
        st = el.get("stereotype", "")
        if st:
            stereotypes[_stereotype_slug(st)] = st
    return {
        "packages": [{"slug": slug, "name": name} for slug, name in sorted(packages.items())],
        "stereotypes": [{"slug": slug, "name": name} for slug, name in sorted(stereotypes.items())],
        "health": [
            {"value": "ok", "label": "OK"},
            {"value": "warning", "label": "Warning"},
            {"value": "error", "label": "Error"},
        ],
    }


def build_mock_filter_chips(
    params: dict[str, Any], options: dict[str, list]
) -> list[dict[str, str]]:
    """Human-readable active filter chips for the canvas toolbar."""
    chips: list[dict[str, str]] = []
    if params.get("loaded_view_name"):
        chips.append({"key": "view", "label": params["loaded_view_name"]})
    if params.get("packages"):
        labels = [
            next((p["name"] for p in options["packages"] if p["slug"] == slug), slug)
            for slug in params["packages"]
        ]
        chips.append({"key": "packages", "label": "Packages: " + ", ".join(labels)})
    if params.get("element_stereotypes"):
        labels = [
            next((s["name"] for s in options["stereotypes"] if s["slug"] == slug), slug)
            for slug in params["element_stereotypes"]
        ]
        chips.append({"key": "element_stereotypes", "label": "Elements: " + ", ".join(labels)})
    if params.get("relationship_stereotypes"):
        chips.append(
            {
                "key": "relationship_stereotypes",
                "label": "Relationships: " + ", ".join(params["relationship_stereotypes"]),
            }
        )
    return chips


def build_package_tree(elements: list[dict]) -> list[dict]:
    """Adapt mock element dicts (``package`` display name) for shared tree builder."""
    adapted = [
        {
            **element,
            "package_slug": element.get("package_slug") or element.get("package", "").lower(),
            "package": element.get("package", ""),
        }
        for element in elements
    ]
    return _build_package_tree(adapted)


MOCK_CHANGESETS = [
    {
        "id": 1,
        "run_id": "run-003",
        "source": "ratatosk",
        "submitted": "2026-07-14 09:12",
        "operations": 6,
        "mode": "manual",
        "status": "pending",
        "summary": (
            "I analysed 3 services, 12 modules, and 4 external dependencies. "
            "The model now contains 16 elements and 24 relationships across the Technology package. "
            "3 operations are awaiting your review — mainly around module-to-service ownership."
        ),
        "ops": [
            {
                "id": 1,
                "op": "Add Element",
                "detail": '"Notification Service" → Container / Technology',
                "confidence": 0.92,
                "status": "pending",
            },
            {
                "id": 2,
                "op": "Link Element",
                "detail": "Notification Service →depends_on→ Payment API",
                "confidence": 0.91,
                "status": "pending",
            },
            {
                "id": 3,
                "op": "Add to Diagram",
                "detail": "Notification Service → Container Diagram C1",
                "confidence": 0.65,
                "status": "pending",
            },
            {
                "id": 4,
                "op": "Update Element",
                "detail": "Order Domain: owner → fulfillment-team (was: payments-team)",
                "confidence": 0.88,
                "status": "pending",
            },
            {
                "id": 5,
                "op": "Delete Element",
                "detail": "LegacyBatch (removed module — 0 active relationships)",
                "confidence": 0.95,
                "status": "pending",
            },
            {
                "id": 6,
                "op": "Add Relationship",
                "detail": "Mobile App →calls→ Notification Service",
                "confidence": 0.78,
                "status": "pending",
            },
        ],
    },
    {
        "id": 2,
        "run_id": "run-002",
        "source": "human",
        "submitted": "2026-07-13 14:45",
        "operations": 2,
        "mode": "auto",
        "status": "applied",
        "summary": "Manual element creation: Fulfillment Worker component added with 2 outbound relationships.",
        "ops": [
            {
                "id": 1,
                "op": "Add Element",
                "detail": '"Fulfillment Worker" → Component / Application',
                "confidence": 1.0,
                "status": "accepted",
            },
            {
                "id": 2,
                "op": "Add Relationship",
                "detail": "Fulfillment Worker →reads_from→ PostgreSQL",
                "confidence": 1.0,
                "status": "accepted",
            },
        ],
    },
    {
        "id": 3,
        "run_id": "run-001",
        "source": "ratatosk",
        "submitted": "2026-07-10 08:00",
        "operations": 21,
        "mode": "auto",
        "status": "applied",
        "summary": "Initial bootstrap: 16 elements and 18 relationships added across Technology and Application packages.",
        "ops": [],
    },
]

MOCK_RUNS = [
    {
        "id": 3,
        "trigger": "ratatosk bootstrap ./repo --model Yggdrasil",
        "status": "complete",
        "started": "2026-07-14 09:10",
        "duration": "2m 14s",
        "candidates": 22,
        "operations": 6,
        "changeset_id": 1,
    },
    {
        "id": 2,
        "trigger": "manual GUI create",
        "status": "complete",
        "started": "2026-07-13 14:44",
        "duration": "0m 08s",
        "candidates": 2,
        "operations": 2,
        "changeset_id": 2,
    },
    {
        "id": 1,
        "trigger": "ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4",
        "status": "complete",
        "started": "2026-07-10 08:00",
        "duration": "4m 31s",
        "candidates": 48,
        "operations": 21,
        "changeset_id": 3,
    },
]

MOCK_TOKENS = [
    {
        "id": 1,
        "name": "laptop-ratatosk",
        "created": "2026-06-01",
        "last_used": "2026-07-14",
        "scope": "read-write",
    },
    {
        "id": 2,
        "name": "cursor-mcp",
        "created": "2026-06-15",
        "last_used": "2026-07-13",
        "scope": "read-only",
    },
]

# ─── Form option lists (EDIT screens pre-select the current value) ──────────

ELEMENT_STEREOTYPE_OPTIONS = ["System", "Container", "Component", "Person", "External"]
ELEMENT_PACKAGE_OPTIONS = ["Context", "Technology", "Application", "Code"]
RELATIONSHIP_EDGE_STEREOTYPE_OPTIONS = ["calls", "depends_on", "serves", "reads_from", "contains"]

# ─── Views ───────────────────────────────────────────────────────────────────


def auth_login(request):
    """AUTH-LOGIN-1: Login form."""
    logger.info("Mockup: auth_login | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/auth/login.html", {})


def auth_token(request):
    """AUTH-TOKEN-1: API token management."""
    logger.info("Mockup: auth_token | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/auth/token.html", {"tokens": MOCK_TOKENS})


def munin_briefing(request):
    """MUNIN-BRIEFING-1: Post-run architectural briefing."""
    logger.info("Mockup: munin_briefing | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/munin/briefing.html",
        {
            "run": MOCK_RUNS[0],
            "changeset": MOCK_CHANGESETS[0],
            "auto_applied": 37,
            "queued": 3,
            "skipped": 2,
        },
    )


def build_table_columns_from_params(params: dict[str, Any]) -> list[dict[str, str]]:
    """Derive table columns from stereotype field selections in the active View.

    :param params: Parsed browse params including ``field_map``.
    :return: Column metadata for the results table.
    """
    cols = ["name", "stereotype"]
    seen = set(cols)
    field_map = params.get("field_map") or {}
    for st in params.get("element_stereotypes") or list(field_map.keys()):
        for path in field_map.get(st, []):
            if path not in seen:
                seen.add(path)
                cols.append(path)
    if len(cols) <= 2:
        cols.extend(["owner", "package"])
    return build_mock_table_columns({"table_columns": cols})


def view_browse(request):
    """VIEW-BROWSE-1: View Browser — three-panel explorer (navigator + canvas + inspector)."""
    logger.info("Mockup: view_browse | user=%s", getattr(request.user, "username", "anonymous"))
    elements_all = MOCK_VIEW_BROWSER_ELEMENTS
    params = parse_mock_browse_params(request, MOCK_MODEL_SLUG)
    if params.get("field_map"):
        field_map = params["field_map"]
    else:
        field_map = {}
        for section in build_view_field_sections(
            params.get("element_stereotypes") or [],
            params.get("relationship_stereotypes") or [],
        ):
            field_map[section["slug"]] = list(section["checked_paths"])
    params = dict(params)
    params["field_map"] = field_map
    elements = filter_mock_elements(elements_all, params)
    package_options = build_mock_filter_options(elements_all)["packages"]
    scoped_stereotypes = build_package_scoped_filter_options(
        elements_all,
        MOCK_VIEW_BROWSER_RELATIONSHIPS,
        params.get("packages"),
    )
    filter_options = {
        "packages": package_options,
        "stereotypes": scoped_stereotypes["stereotypes"],
        "relationship_stereotypes": scoped_stereotypes["relationship_stereotypes"],
    }
    chips = build_mock_filter_chips(params, filter_options)
    views_for_model = [v for v in MOCK_BROWSE_VIEWS if v["model_slug"] == MOCK_MODEL_SLUG]
    view_field_sections = build_view_field_sections(
        params.get("element_stereotypes") or [],
        params.get("relationship_stereotypes") or [],
        params.get("field_map"),
    )
    table_columns = build_table_columns_from_params(params)
    content_display = field_map_to_content_display(
        field_map,
        params.get("element_stereotypes") or [],
        params.get("relationship_stereotypes") or [],
    )
    visible_ids = {el["id"] for el in elements}
    scoped_relationships = [
        rel
        for rel in MOCK_VIEW_BROWSER_RELATIONSHIPS
        if rel["from_id"] in visible_ids or rel["to_id"] in visible_ids
    ]
    display_elements, display_relationships = enrich_mock_canvas_rows(
        elements,
        scoped_relationships,
        table_columns,
        content_display,
    )

    logger.info(
        "Mockup: view_browse state | mode=%s depth=%s view=%s filters=%s visible=%s",
        params["mode"],
        params["depth"],
        params.get("loaded_view_name") or "-",
        {
            "packages": params.get("packages"),
            "element_stereotypes": params.get("element_stereotypes"),
            "relationship_stereotypes": params.get("relationship_stereotypes"),
        },
        len(elements),
    )

    return render(
        request,
        "mockups/view/browse.html",
        {
            "elements": display_elements,
            "elements_all": elements_all,
            "relationships": display_relationships,
            "packages": build_package_tree(elements),
            "model_name": "Yggdrasil",
            "model_slug": MOCK_MODEL_SLUG,
            "element_count": len(elements),
            "relationship_count": len(scoped_relationships),
            "view_mode": params["mode"],
            "current_depth": params["depth"],
            "max_depth": MOCK_MAX_DEPTH,
            "active_filters": params,
            "filter_options": filter_options,
            "filter_chips": chips,
            "browse_views": views_for_model,
            "mock_browse_url": request.path,
            "view_field_sections": view_field_sections,
            "table_columns": table_columns,
            "loaded_viewport_json": json.dumps(params.get("viewport") or {}),
            "baseline_browse_view": params.get("baseline_browse_view") or "",
            "stereotype_field_schema": MOCK_STEREOTYPE_FIELD_SCHEMA,
            "content_display": content_display,
            "canvas_payload": {
                "elements": display_elements,
                "relationships": display_relationships,
            },
            "filter_catalog": build_filter_catalog_payload(
                elements_all, MOCK_VIEW_BROWSER_RELATIONSHIPS
            ),
        },
    )


def view_export(request):
    """EXPORT-BRIEFING-1: Export modal."""
    logger.info("Mockup: view_export | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/view/export.html",
        {
            "element_count": len(MOCK_ELEMENTS),
            "relationship_count": len(MOCK_RELATIONSHIPS),
        },
    )


def view_history(request):
    """VIEW-HISTORY-1: Model history / diff."""
    logger.info("Mockup: view_history | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/view/history.html", {"changesets": MOCK_CHANGESETS})


def element_list(request):
    """ELEMENT-LIST+FIND-1: Elements list & search."""
    logger.info("Mockup: element_list | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/element/list.html",
        {
            "elements": MOCK_ELEMENTS,
            "element_count": len(MOCK_ELEMENTS),
        },
    )


def element_view(request, id):
    """ELEMENT-VIEW_ELEMENT-1: Element detail."""
    logger.info(
        "Mockup: element_view | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    element = next((e for e in MOCK_ELEMENTS if e["id"] == id), MOCK_ELEMENTS[0])
    rels = [r for r in MOCK_RELATIONSHIPS if r["from_id"] == id or r["to_id"] == id]
    return render(request, "mockups/element/view.html", {"element": element, "relationships": rels})


def element_create(request):
    """ELEMENT-CREATE_ELEMENT-1: Create element form."""
    logger.info("Mockup: element_create | user=%s", getattr(request.user, "username", "anonymous"))
    return render(request, "mockups/element/create.html", {"elements": MOCK_ELEMENTS})


def element_edit(request, id):
    """ELEMENT-EDIT_ELEMENT-1: Edit element form."""
    logger.info(
        "Mockup: element_edit | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    element = next((e for e in MOCK_ELEMENTS if e["id"] == id), MOCK_ELEMENTS[0])
    return render(
        request,
        "mockups/element/edit.html",
        {
            "element": element,
            "elements": MOCK_ELEMENTS,
            "stereotype_options": ELEMENT_STEREOTYPE_OPTIONS,
            "package_options": ELEMENT_PACKAGE_OPTIONS,
        },
    )


def relationship_list(request):
    """RELATIONSHIP-LIST+FIND-1: Relationships list."""
    logger.info(
        "Mockup: relationship_list | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(
        request,
        "mockups/relationship/list.html",
        {
            "relationships": MOCK_RELATIONSHIPS,
            "relationship_count": len(MOCK_RELATIONSHIPS),
        },
    )


def relationship_view(request, id):
    """RELATIONSHIP-VIEW_RELATIONSHIP-1: Relationship detail."""
    logger.info(
        "Mockup: relationship_view | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    rel = next((r for r in MOCK_RELATIONSHIPS if r["id"] == id), MOCK_RELATIONSHIPS[0])
    return render(request, "mockups/relationship/view.html", {"relationship": rel})


def relationship_create(request):
    """RELATIONSHIP-CREATE_RELATIONSHIP-1: Create relationship form."""
    logger.info(
        "Mockup: relationship_create | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(request, "mockups/relationship/create.html", {"elements": MOCK_ELEMENTS})


def relationship_edit(request, id):
    """RELATIONSHIP-EDIT_RELATIONSHIP-1: Edit relationship form."""
    logger.info(
        "Mockup: relationship_edit | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    rel = next((r for r in MOCK_RELATIONSHIPS if r["id"] == id), MOCK_RELATIONSHIPS[0])
    return render(
        request,
        "mockups/relationship/edit.html",
        {
            "relationship": rel,
            "elements": MOCK_ELEMENTS,
            "edge_stereotype_options": RELATIONSHIP_EDGE_STEREOTYPE_OPTIONS,
        },
    )


def changeset_list(request):
    """CHANGESET-LIST+FIND-1: ChangeSet queue."""
    logger.info("Mockup: changeset_list | user=%s", getattr(request.user, "username", "anonymous"))
    return render(
        request,
        "mockups/changeset/list.html",
        {
            "changesets": MOCK_CHANGESETS,
            "changeset_count": len(MOCK_CHANGESETS),
        },
    )


def changeset_view(request, id):
    """CHANGESET-VIEW_CHANGESET-1: ChangeSet review."""
    logger.info(
        "Mockup: changeset_view | id=%s user=%s", id, getattr(request.user, "username", "anonymous")
    )
    cs = next((c for c in MOCK_CHANGESETS if c["id"] == id), MOCK_CHANGESETS[0])
    return render(request, "mockups/changeset/view.html", {"changeset": cs})


def ratatosk_run_list(request):
    """RATATOSK_RUN-LIST+FIND-1: Run list."""
    logger.info(
        "Mockup: ratatosk_run_list | user=%s", getattr(request.user, "username", "anonymous")
    )
    return render(
        request,
        "mockups/ratatosk_run/list.html",
        {
            "runs": MOCK_RUNS,
            "run_count": len(MOCK_RUNS),
        },
    )


def ratatosk_run_view(request, id):
    """RATATOSK_RUN-VIEW_RATATOSK_RUN-1: Run detail."""
    logger.info(
        "Mockup: ratatosk_run_view | id=%s user=%s",
        id,
        getattr(request.user, "username", "anonymous"),
    )
    run = next((r for r in MOCK_RUNS if r["id"] == id), MOCK_RUNS[0])
    cs = next((c for c in MOCK_CHANGESETS if c.get("id") == run.get("changeset_id")), None)
    return render(request, "mockups/ratatosk_run/view.html", {"run": run, "changeset": cs})
