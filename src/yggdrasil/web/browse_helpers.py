"""View Browser helpers — filter parsing and template context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from django.http import HttpRequest

from yggdrasil.graph import browse_service


@dataclass(frozen=True)
class ViewBrowseParams:
    """Parsed query parameters for VIEW-BROWSE-1."""

    model_slug: str
    stereotype: str | None
    package: str | None
    health: str | None
    as_of: str | None


def parse_view_browse_params(request: HttpRequest) -> ViewBrowseParams:
    """
    Parse filter query params from a View Browser request.

    :param request: Django HTTP request.
    :return: Normalized browse parameters.
    """
    return ViewBrowseParams(
        model_slug=browse_service.DEFAULT_MODEL_SLUG,
        stereotype=_blank_to_none(request.GET.get("stereotype")),
        package=_blank_to_none(request.GET.get("package")),
        health=_blank_to_none(request.GET.get("health")),
        as_of=_blank_to_none(request.GET.get("as_of")),
    )


def build_view_browse_context(request: HttpRequest, params: ViewBrowseParams) -> dict[str, Any]:
    """
    Build template context for View Browser full page or HTMX partial.

    :param request: Authenticated request (for user_id in service logs).
    :param params: Parsed browse parameters.
    :return: Context dict with elements, filter options, and active filters.
    """
    try:
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
    except ValueError:
        elements = []
        element_count = 0
        options = {"packages": [], "stereotypes": [], "health": []}
    return {
        "elements": elements,
        "element_count": element_count,
        "filter_options": options,
        "active_filters": params,
        "model_slug": params.model_slug,
    }


def _row_from_summary(item: dict[str, Any]) -> dict[str, Any]:
    """Map browse_service summary dict to table row fields."""
    return {
        "id": item["id"],
        "name": item["name"],
        "stereotype": item["stereotype"],
        "package": item["package"],
        "owner": item["owner"],
        "health": item["health"],
        "source": item["source"],
    }


def _blank_to_none(value: str | None) -> str | None:
    """Treat empty query values as no filter."""
    if value is None or value.strip() == "":
        return None
    return value.strip()
