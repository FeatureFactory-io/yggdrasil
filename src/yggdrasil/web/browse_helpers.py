"""View Browser helpers — filter parsing and template context."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest

from yggdrasil.graph import browse_service

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


@dataclass(frozen=True)
class ViewBrowseParams:
    """Parsed query parameters for VIEW-BROWSE-1."""

    model_slug: str
    stereotype: str | None
    package: str | None
    health: str | None
    as_of: str | None
    view_mode: str


def parse_view_browse_params(request: HttpRequest, model_slug: str) -> ViewBrowseParams:
    """
    Parse filter query parameters from a View Browser request.

    :param request: Django HTTP request.
    :param model_slug: Model slug from the URL path. Example: ``"yggdrasil"``.
    :return: Normalized browse parameters.
    """
    raw_view = _blank_to_none(request.GET.get("view")) or "table"
    view_mode = raw_view if raw_view in VALID_VIEW_MODES else "table"
    return ViewBrowseParams(
        model_slug=model_slug,
        stereotype=_blank_to_none(request.GET.get("stereotype")),
        package=_blank_to_none(request.GET.get("package")),
        health=_blank_to_none(request.GET.get("health")),
        as_of=_blank_to_none(request.GET.get("as_of")),
        view_mode=view_mode,
    )


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
        "packages": [],
        "model_name": "",
        "filter_options": {"packages": [], "stereotypes": [], "health": []},
        "active_filters": ViewBrowseParams(
            model_slug="",
            stereotype=None,
            package=None,
            health=None,
            as_of=None,
            view_mode="table",
        ),
        "model_slug": "",
        "view_mode": "table",
        "readable_models": readable_models,
        "switcher_disabled": True,
        "no_models": True,
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
    try:
        ymodel = browse_service.resolve_model(params.model_slug)
        model_name = ymodel.name
        result = browse_service.list_elements(
            model_slug=params.model_slug,
            stereotype=params.stereotype,
            package=params.package,
            health=params.health,
            as_of=params.as_of,
            limit=200,
            user_id=request.user.pk,
        )
        options = browse_service.list_filter_options(model_slug=params.model_slug)
        elements = [_row_from_summary(item) for item in result.items]
        element_count = result.total
        packages = build_package_tree(elements)
    except ValueError:
        elements = []
        element_count = 0
        packages = []
        options = {"packages": [], "stereotypes": [], "health": []}

    logger.info(
        "build_view_browse_context | package_count=%s element_count=%s model_slug=%s",
        len(packages),
        element_count,
        params.model_slug,
    )
    return {
        "elements": elements,
        "element_count": element_count,
        "packages": packages,
        "model_name": model_name,
        "filter_options": options,
        "active_filters": params,
        "model_slug": params.model_slug,
        "view_mode": params.view_mode,
        "readable_models": readable_models,
        "switcher_disabled": switcher_disabled,
        "no_models": False,
    }


def _row_from_summary(item: dict[str, Any]) -> dict[str, Any]:
    """Map browse_service summary dict to table/navigator row fields."""
    return {
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
    }


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
