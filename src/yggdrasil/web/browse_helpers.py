"""View Browser helpers — filter parsing and template context."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.http import HttpRequest

    from yggdrasil.graph.models import YggdrasilModel

from urllib.parse import urlencode

from django.urls import reverse

from yggdrasil.graph import browse_content, browse_service, browse_view_service

logger = logging.getLogger("yggdrasil.web")

PACKAGE_DISPLAY_ORDER = ("context", "application", "technology", "code")


CONFIDENCE_BAND_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (0.85, "high"),
    (0.60, "medium"),
    (0.40, "low"),
)


def confidence_band(confidence: float) -> str:
    """
    Map a 0.0-1.0 confidence score to IA §15.6 semantic band.

    :param confidence: Confidence score in [0.0, 1.0].
    :return: One of ``high``, ``medium``, ``low``, ``vlow``.
    """
    for threshold, band in CONFIDENCE_BAND_THRESHOLDS:
        if confidence >= threshold:
            return band
    return "vlow"


def enrich_confidence_fields(item: dict[str, Any]) -> dict[str, Any]:
    """
    Attach ``conf_pct`` and ``conf_band`` for template confidence bars.

    :param item: Dict containing ``confidence`` float.
    :return: Shallow copy with display fields added.
    """
    enriched = dict(item)
    confidence = float(enriched.get("confidence", 1.0))
    enriched["conf_pct"] = round(confidence * 100)
    enriched["conf_band"] = confidence_band(confidence)
    return enriched


VALID_VIEW_MODES = frozenset({"table", "graph"})
DEFAULT_VIEW_MODE = "graph"


@dataclass(frozen=True)
class ViewBrowseParams:
    """Parsed query parameters for VIEW-BROWSE-1."""

    model_slug: str
    packages: tuple[str, ...] = ()
    element_stereotypes: tuple[str, ...] = ()
    relationship_stereotypes: tuple[str, ...] = ()
    health: str | None = None
    as_of: str | None = None
    view_mode: str = DEFAULT_VIEW_MODE
    depth: int = browse_service.DEFAULT_DEPTH
    field_map: dict[str, tuple[str, ...]] = field(default_factory=dict)
    viewport: dict[str, Any] | None = None
    browse_view: str | None = None
    loaded_view_name: str | None = None

    @property
    def package(self) -> str | None:
        """First selected package slug (legacy single-select callers)."""
        return self.packages[0] if self.packages else None

    @property
    def stereotype(self) -> str | None:
        """First selected element stereotype slug (legacy single-select callers)."""
        return self.element_stereotypes[0] if self.element_stereotypes else None


def _parse_view_mode(request: HttpRequest) -> str:
    """
    Parse presentation mode from ``?mode=`` with legacy ``?view=`` fallback.

    :param request: Django HTTP request.
    :return: ``graph`` or ``table``.
    """
    raw = _blank_to_none(request.GET.get("mode")) or _blank_to_none(request.GET.get("view"))
    if raw in VALID_VIEW_MODES:
        return raw
    return DEFAULT_VIEW_MODE


def _get_query_list(query: Any, key: str) -> tuple[str, ...]:
    """
    Read repeated query values, skipping blanks.

    :param query: ``request.GET`` or ``request.POST`` mapping.
    :param key: Parameter name. Example: ``"package"``.
    :return: Non-empty trimmed values.
    """
    getlist = getattr(query, "getlist", None)
    if getlist is None:
        raw = query.get(key)
        return (
            (_blank_to_none(str(raw)),)
            if _blank_to_none(str(raw) if raw is not None else None)
            else ()
        )
    values = [_blank_to_none(item) for item in getlist(key)]
    return tuple(item for item in values if item)


def _field_map_from_query(query: Any) -> dict[str, tuple[str, ...]]:
    """Normalize ``field_{stereotype}`` params to immutable tuples."""
    parsed = browse_content.parse_field_map_from_query(query)
    return {slug: tuple(paths) for slug, paths in parsed.items()}


def parse_view_browse_params(request: HttpRequest, model_slug: str) -> ViewBrowseParams:
    """
    Parse filter query parameters from a View Browser request.

    :param request: Django HTTP request.
    :param model_slug: Model slug from the URL path. Example: ``"yggdrasil"``.
    :return: Normalized browse parameters.
    """
    view_mode = _parse_view_mode(request)
    packages = _get_query_list(request.GET, "package")
    element_stereotypes = _get_query_list(request.GET, "stereotype")
    relationship_stereotypes = _get_query_list(request.GET, "edge_stereotype")
    return ViewBrowseParams(
        model_slug=model_slug,
        packages=packages,
        element_stereotypes=element_stereotypes,
        relationship_stereotypes=relationship_stereotypes,
        health=_blank_to_none(request.GET.get("health")),
        as_of=_blank_to_none(request.GET.get("as_of")),
        view_mode=view_mode,
        depth=_parse_depth(request.GET.get("depth")),
        field_map=_field_map_from_query(request.GET),
    )


def apply_browse_view_expansion(
    request: HttpRequest,
    user: AbstractBaseUser,
    ymodel: YggdrasilModel,
    params: ViewBrowseParams,
) -> ViewBrowseParams:
    """
    Expand ``?browse_view=`` into filter params; explicit query values win.

    :param request: Django HTTP request.
    :param user: Authenticated user loading the View.
    :param ymodel: Active YggdrasilModel instance.
    :param params: Base parsed params (may include ``browse_view`` slug only).
    :return: Params with filters/depth/mode from saved payload when resolved.
    """
    browse_view_slug = _blank_to_none(request.GET.get("browse_view"))
    if not browse_view_slug:
        return params

    logger.info(
        "browse_helpers.apply_browse_view_expansion | entry | browse_view=%s model_slug=%s user_pk=%s",
        browse_view_slug,
        ymodel.slug,
        user.pk,
    )
    saved = browse_view_service.resolve_view_for_load(user, ymodel, browse_view_slug)
    if saved is None:
        return params

    expanded = browse_view_service.expand_to_query_params(saved)
    packages = _get_query_list(request.GET, "package")
    if not packages and expanded.get("package"):
        packages = tuple(expanded["package"])
    element_stereotypes = _get_query_list(request.GET, "stereotype")
    if not element_stereotypes and expanded.get("stereotype"):
        element_stereotypes = tuple(expanded["stereotype"])
    relationship_stereotypes = _get_query_list(request.GET, "edge_stereotype")
    if not relationship_stereotypes and expanded.get("edge_stereotype"):
        relationship_stereotypes = tuple(expanded["edge_stereotype"])
    health = params.health
    as_of = params.as_of
    view_mode = _parse_view_mode(request)
    if request.GET.get("mode") is None and request.GET.get("view") is None:
        view_mode = expanded.get("mode", [params.view_mode])[0]
    depth = params.depth
    if request.GET.get("depth") is None:
        depth = int(expanded.get("depth", [str(params.depth)])[0])
    query_field_map = _field_map_from_query(request.GET)
    field_map = query_field_map if query_field_map else _field_map_from_expanded(expanded)
    viewport = params.viewport
    if not query_field_map:
        viewport = _viewport_from_expanded(expanded) or viewport

    merged = ViewBrowseParams(
        model_slug=params.model_slug,
        packages=packages,
        element_stereotypes=element_stereotypes,
        relationship_stereotypes=relationship_stereotypes,
        health=health,
        as_of=as_of,
        view_mode=view_mode,
        depth=depth,
        field_map=field_map,
        viewport=viewport,
        browse_view=browse_view_slug,
        loaded_view_name=saved.name,
    )
    logger.info(
        "browse_helpers.apply_browse_view_expansion | exit | browse_view=%s expanded=true depth=%s package=%s",
        browse_view_slug,
        merged.depth,
        merged.package,
    )
    return merged


def _field_map_from_expanded(expanded: dict[str, list[str]]) -> dict[str, tuple[str, ...]]:
    """Extract field_map tuples from expanded query param lists."""
    field_map: dict[str, tuple[str, ...]] = {}
    for key, values in expanded.items():
        if not str(key).startswith("field_"):
            continue
        slug = str(key)[6:]
        if slug and values:
            field_map[slug] = tuple(values)
    return field_map


def _viewport_from_expanded(expanded: dict[str, list[str]]) -> dict[str, Any] | None:
    """Parse optional viewport JSON from expanded query params."""
    raw_values = expanded.get("viewport")
    if not raw_values:
        return None
    try:
        parsed = json.loads(raw_values[0])
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def user_can_save_views(user: AbstractBaseUser) -> bool:
    """
    Return whether ``user`` may save or delete named Views (architect role).

    :param user: Authenticated user.
    :return: True when user is superuser or in the architect group.
    """
    if user.is_superuser:
        return True
    return user.groups.filter(name="architect").exists()


def build_payload_from_browse_params(params: ViewBrowseParams) -> dict:
    """
    Build a BrowseView payload v1 from current browse params.

    :param params: Active browse parameters.
    :return: Payload dict for ``browse_view_service.save_view``.
    """
    filters: dict[str, list[str]] = {
        "packages": list(params.packages),
        "element_stereotypes": list(params.element_stereotypes),
        "relationship_stereotypes": list(params.relationship_stereotypes),
    }
    payload: dict[str, Any] = {
        "filters": filters,
        "levels": {"depth": params.depth},
        "presentation": params.view_mode,
        "content": {
            "field_map": {slug: list(paths) for slug, paths in params.field_map.items()},
        },
    }
    if params.viewport is not None:
        payload["viewport"] = params.viewport
    return payload


def _parse_depth(raw: str | None) -> int:
    """
    Parse ``?depth=`` query param.

    :param raw: Raw query value or None.
    :return: Integer depth >= 1 (default ``DEFAULT_DEPTH``).
    """
    if raw is None or raw.strip() == "":
        return browse_service.DEFAULT_DEPTH
    try:
        depth = int(raw.strip())
    except ValueError:
        return browse_service.DEFAULT_DEPTH
    return max(depth, 1)


def build_empty_browse_context(request: HttpRequest) -> dict[str, Any]:
    """
    Build template context when the user can read zero Models.

    :param request: Authenticated request.
    :return: Empty browse context with switcher disabled.
    """
    readable_models = list(browse_service.list_readable_models(request.user))
    logger.info(
        "build_empty_browse_context | user_pk=%s readable_count=%s",
        request.user.pk,
        len(readable_models),
    )
    return {
        "elements": [],
        "element_count": 0,
        "traversal_roots": [],
        "max_depth": 1,
        "current_depth": browse_service.DEFAULT_DEPTH,
        "model_name": "",
        "filter_options": {"packages": [], "stereotypes": [], "health": []},
        "active_filters": ViewBrowseParams(
            model_slug="",
            view_mode=DEFAULT_VIEW_MODE,
            depth=browse_service.DEFAULT_DEPTH,
        ),
        "model_slug": "",
        "view_mode": DEFAULT_VIEW_MODE,
        "readable_models": readable_models,
        "switcher_disabled": True,
        "no_models": True,
        "browse_views": [],
        "browse_view_entries": [],
        "can_save_views": False,
        "view_field_sections": [],
        "table_columns": browse_content.build_table_columns(
            element_stereotypes=[],
            field_map={},
        ),
        "loaded_viewport_json": None,
    }


def build_package_tree(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Group flat element rows into package buckets for the navigator tree.

    :param elements: Row dicts with ``package_slug`` and ``package`` display name.
    :return: Ordered list[Any] of ``{"name", "slug", "elements": [...]}`` dicts.
    """
    buckets: dict[str, list[dict[str, Any]]] = {}
    display_names: dict[str, str] = {}
    for element in elements:
        pkg_slug = _package_key(element)
        if not pkg_slug:
            continue
        buckets.setdefault(pkg_slug, []).append(element)
        if pkg_slug not in display_names and element.get("package"):
            display_names[pkg_slug] = element["package"]

    tree: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pkg_slug in PACKAGE_DISPLAY_ORDER:
        if pkg_slug in buckets:
            tree.append(_package_node(pkg_slug, buckets[pkg_slug], display_names))
            seen.add(pkg_slug)
    for pkg_slug in sorted(buckets.keys()):
        if pkg_slug not in seen:
            tree.append(_package_node(pkg_slug, buckets[pkg_slug], display_names))

    logger.info("build_package_tree | package_count=%s element_count=%s", len(tree), len(elements))
    return tree


def build_traversal_tree(
    node_rows: list[dict[str, Any]],
    parent_map: dict[int, int | None],
    root_ids: frozenset[int],
) -> list[dict[str, Any]]:
    """
    Build nested navigator tree from BFS parent map.

    :param node_rows: Flat element row dicts with ``id`` and ``slug``.
    :param parent_map: Child PK -> parent PK (roots map to None).
    :param root_ids: Root element PKs from BFS.
    :return: Root nodes with nested ``children`` lists.
    """
    by_id = {row["id"]: row for row in node_rows}
    children_map: dict[int, list[int]] = {}
    for child_id, parent_id in parent_map.items():
        if parent_id is not None and child_id in by_id and parent_id in by_id:
            children_map.setdefault(parent_id, []).append(child_id)

    def build_node(pk: int) -> dict[str, Any]:
        row = dict(by_id[pk])
        child_pks = sorted(
            children_map.get(pk, []),
            key=lambda child_pk: by_id[child_pk]["name"],
        )
        row["children"] = [build_node(child_pk) for child_pk in child_pks]
        row["expanded"] = pk in root_ids
        return row

    roots = sorted(
        (pk for pk in root_ids if pk in by_id),
        key=lambda pk: by_id[pk]["name"],
    )
    tree = [build_node(pk) for pk in roots]
    logger.info(
        "build_traversal_tree | tree_root_count=%s element_count=%s",
        len(tree),
        len(node_rows),
    )
    return tree


def build_view_browse_context(request: HttpRequest, params: ViewBrowseParams) -> dict[str, Any]:
    """
    Build template context for View Browser full page or HTMX partial.

    :param request: Authenticated request (for user_id in service logs).
    :param params: Parsed browse parameters.
    :return: Context dict[str, Any] with elements, packages, filter options, and active filters.
    """
    readable_models = list(browse_service.list_readable_models(request.user))
    switcher_disabled = len(readable_models) <= 1
    model_name = params.model_slug.title()
    ymodel = None
    browse_views: list = []
    browse_view_entries: list[dict[str, Any]] = []
    field_map_dict = {slug: list(paths) for slug, paths in params.field_map.items()}
    view_field_sections = browse_content.build_view_field_sections(
        list(params.element_stereotypes),
        list(params.relationship_stereotypes),
        field_map_dict,
    )
    table_columns = browse_content.build_table_columns(
        element_stereotypes=list(params.element_stereotypes),
        field_map=field_map_dict,
    )

    try:
        ymodel = browse_service.resolve_model(params.model_slug)
        model_name = ymodel.name
        browse_views = list(browse_view_service.list_views(request.user, ymodel))
        browse_view_entries = [_browse_view_entry(params.model_slug, view) for view in browse_views]
        scoped = browse_service.subgraph_from_roots(
            model_slug=params.model_slug,
            stereotype=params.stereotype,
            package=params.package,
            health=params.health,
            packages=params.packages,
            stereotypes=params.element_stereotypes,
            relationship_stereotypes=params.relationship_stereotypes,
            depth=params.depth,
            user_id=request.user.pk,
            field_map={slug: list(paths) for slug, paths in params.field_map.items()},
        )
        options = browse_service.list_filter_options(model_slug=params.model_slug)
        if params.packages:
            options = browse_service.build_package_scoped_filter_options(
                model_slug=params.model_slug,
                packages=params.packages,
            )
        elements = [
            _row_from_summary(item, table_columns, field_map_dict) for item in scoped.node_summaries
        ]
        element_count = len(elements)
        traversal_roots = build_traversal_tree(
            elements,
            scoped.parent_map,
            scoped.root_ids,
        )
        max_depth = scoped.max_depth
        current_depth = params.depth
    except ValueError:
        elements = []
        element_count = 0
        traversal_roots = []
        max_depth = 1
        current_depth = params.depth
        options = {"packages": [], "stereotypes": [], "relationship_stereotypes": [], "health": []}

    logger.info(
        "build_view_browse_context | depth=%s element_count=%s tree_root_count=%s model_slug=%s",
        current_depth,
        element_count,
        len(traversal_roots),
        params.model_slug,
    )
    return {
        "elements": elements,
        "element_count": element_count,
        "traversal_roots": traversal_roots,
        "max_depth": max_depth,
        "current_depth": current_depth,
        "model_name": model_name,
        "filter_options": options,
        "active_filters": params,
        "model_slug": params.model_slug,
        "view_mode": params.view_mode,
        "readable_models": readable_models,
        "switcher_disabled": switcher_disabled,
        "no_models": False,
        "browse_views": browse_views,
        "browse_view_entries": browse_view_entries,
        "can_save_views": user_can_save_views(request.user),
        "view_field_sections": view_field_sections,
        "table_columns": table_columns,
        "loaded_viewport_json": params.viewport if params.view_mode == "graph" else None,
    }


def _browse_view_entry(model_slug: str, view: Any) -> dict[str, Any]:
    """Build template entry with expanded load URL for a saved View."""
    expanded = browse_view_service.expand_to_query_params(view)
    expanded["browse_view"] = [view.slug]
    base = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
    load_url = base + "?" + urlencode(expanded, doseq=True)
    return {"view": view, "load_url": load_url}


def parse_browse_params_from_post(request: HttpRequest, model_slug: str) -> ViewBrowseParams:
    """
    Parse browse filter fields from a save-view POST body.

    :param request: Django HTTP request with POST data.
    :param model_slug: Model slug from the URL path.
    :return: Normalized browse parameters for payload construction.
    """
    raw_mode = request.POST.get("mode") or DEFAULT_VIEW_MODE
    view_mode = raw_mode if raw_mode in VALID_VIEW_MODES else DEFAULT_VIEW_MODE
    packages = _get_query_list(request.POST, "package")
    element_stereotypes = _get_query_list(request.POST, "stereotype")
    relationship_stereotypes = _get_query_list(request.POST, "edge_stereotype")
    field_map = _field_map_from_query(request.POST)
    viewport = _parse_viewport_from_post(request)
    return ViewBrowseParams(
        model_slug=model_slug,
        packages=packages,
        element_stereotypes=element_stereotypes,
        relationship_stereotypes=relationship_stereotypes,
        health=_blank_to_none(request.POST.get("health")),
        as_of=_blank_to_none(request.POST.get("as_of")),
        view_mode=view_mode,
        depth=_parse_depth(request.POST.get("depth")),
        field_map=field_map,
        viewport=viewport,
    )


def _row_from_summary(
    item: dict[str, Any],
    table_columns: list[dict[str, str]] | None = None,
    field_map: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Map browse_service summary dict to table/navigator row fields."""
    row = {
        "id": item["id"],
        "name": item["name"],
        "slug": item["slug"],
        "stereotype": item["stereotype"],
        "stereotype_slug": item["stereotype_slug"],
        "package": item["package"],
        "package_slug": item["package_slug"],
        "owner": item["owner"],
        "health": item["health"],
        "source": item["source"],
        "properties": item.get("properties") or {},
    }
    if table_columns:
        row["table_cells"] = [
            {
                "key": col["key"],
                "value": browse_content.table_cell_display(row, col["key"]),
            }
            for col in table_columns
        ]
    return row


def _parse_viewport_from_post(request: HttpRequest) -> dict[str, Any] | None:
    """Parse optional viewport JSON from save-view POST."""
    raw = (request.POST.get("viewport") or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _package_key(element: dict[str, Any]) -> str:
    """Resolve package slug from a row dict (production or mockup shape)."""
    if element.get("package_slug"):
        return str(element["package_slug"])
    package = element.get("package", "")
    return package.lower() if package else ""


def _package_node(
    pkg_slug: str,
    elements: list[dict[str, Any]],
    display_names: dict[str, str],
) -> dict[str, Any]:
    """Build one package tree node."""
    return {
        "name": display_names.get(pkg_slug, pkg_slug.replace("-", " ").title()),
        "slug": pkg_slug,
        "elements": sorted(elements, key=lambda e: e["name"]),
    }


def _blank_to_none(value: str | None) -> str | None:
    """Treat empty query values as no filter."""
    if value is None or value.strip() == "":
        return None
    return value.strip()
