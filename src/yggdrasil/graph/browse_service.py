"""
Browse/query service for the View Browser and MCP read tools.

Shared ORM layer — web views and MCP tools call these functions; no MCP-specific
logic here (SAO §18.2 Case A Service Bridge).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from django.db.models import Q, QuerySet

from yggdrasil.graph.models import Element, Package, Relationship, Stereotype, YggdrasilModel

logger = logging.getLogger("yggdrasil.graph.browse")

MAX_LIMIT = 200
DEFAULT_MODEL_SLUG = "yggdrasil"


@dataclass(frozen=True)
class BrowseFilters:
    """Filter parameters for element list and subgraph queries."""

    stereotype: str | None = None
    package: str | None = None
    health: str | None = None
    as_of: str | None = None


@dataclass(frozen=True)
class BrowseResult:
    """Paginated element list result."""

    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    as_of: str | None = None


def resolve_model(model_slug: str) -> YggdrasilModel:
    """
    Resolve a model instance by slug or name (case-insensitive).

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :return: Matching ``YggdrasilModel``.
    :raises ValueError: If not found or ambiguous.
    """
    try:
        return YggdrasilModel.objects.get(Q(slug__iexact=model_slug) | Q(name__iexact=model_slug))
    except YggdrasilModel.DoesNotExist as exc:
        msg = f"Model {model_slug!r} not found"
        raise ValueError(msg) from exc
    except YggdrasilModel.MultipleObjectsReturned as exc:
        msg = f"Model {model_slug!r} is ambiguous"
        raise ValueError(msg) from exc


def element_summary(element: Element) -> dict[str, Any]:
    """
    Serialize an element for API/list responses.

    :param element: ORM element with stereotype/package loaded.
    :return: Summary dict including health and source.
    """
    return {
        "id": element.pk,
        "name": element.name,
        "slug": element.slug,
        "stereotype": element.stereotype.name if element.stereotype_id else "",
        "stereotype_slug": element.stereotype.slug if element.stereotype_id else "",
        "package": element.package.name if element.package_id else "",
        "package_slug": element.package.slug if element.package_id else "",
        "owner": element.owner,
        "health": element.health,
        "source": element.source,
        "confidence": element.confidence,
        "properties": element.properties,
    }


def element_row(element: Element) -> dict[str, Any]:
    """
    Serialize an element for View Browser table rows.

    :param element: ORM element.
    :return: Template-friendly row dict.
    """
    summary = element_summary(element)
    return {
        "id": summary["id"],
        "name": summary["name"],
        "stereotype": summary["stereotype"],
        "package": summary["package"],
        "owner": summary["owner"],
        "health": summary["health"],
        "source": summary["source"],
    }


def list_elements(
    *,
    model_slug: str,
    stereotype: str | None = None,
    package: str | None = None,
    health: str | None = None,
    as_of: str | None = None,
    limit: int = 50,
    offset: int = 0,
    user_id: int | None = None,
) -> BrowseResult:
    """
    Return a paginated, filterable element list for a model.

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :param stereotype: Stereotype slug or name filter. Example: ``"container"``
    :param package: Package slug or name filter. Example: ``"technology"``
    :param health: Health status filter. Example: ``"green"``
    :param as_of: Historical snapshot date (metadata only in MVP). Example: ``"2026-01-15"``
    :param limit: Page size (max 200). Example: ``50``
    :param offset: Pagination offset. Example: ``0``
    :param user_id: Authenticated user PK for audit logs. Example: ``42``
    :return: ``BrowseResult`` with element summary dicts.
    :raises ValueError: If model slug not found.
    """
    filters = BrowseFilters(stereotype=stereotype, package=package, health=health, as_of=as_of)
    logger.info(
        "browse_service.list_elements | entry model_slug=%s filters=%s user_id=%s",
        model_slug,
        filters,
        user_id,
    )
    ymodel = resolve_model(model_slug)
    page_limit = min(max(limit, 1), MAX_LIMIT)
    page_offset = max(offset, 0)
    qs = _filtered_queryset(ymodel, filters)
    total = qs.count()
    items = [
        element_summary(el) for el in qs.order_by("name")[page_offset : page_offset + page_limit]
    ]
    logger.info(
        "browse_service.list_elements | exit model_slug=%s total=%s returned_count=%s user_id=%s",
        model_slug,
        total,
        len(items),
        user_id,
    )
    return BrowseResult(
        items=items,
        total=total,
        limit=page_limit,
        offset=page_offset,
        as_of=as_of,
    )


def list_filter_options(*, model_slug: str) -> dict[str, list[dict[str, str]]]:
    """
    Return package and stereotype options for View Browser filter dropdowns.

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :return: ``{"packages": [...], "stereotypes": [...], "health": [...]}``
    :raises ValueError: If model not found.
    """
    ymodel = resolve_model(model_slug)
    packages = [
        {"name": pkg.name, "slug": pkg.slug}
        for pkg in Package.objects.filter(metamodel=ymodel.metamodel).order_by("name")
    ]
    stereotypes = [
        {"name": st.name, "slug": st.slug}
        for st in Stereotype.objects.filter(metamodel=ymodel.metamodel, is_edge=False).order_by(
            "name"
        )
    ]
    health = [{"value": value, "label": label} for value, label in Element.HEALTH_CHOICES]
    return {"packages": packages, "stereotypes": stereotypes, "health": health}


def subgraph_for_elements(
    *,
    model_slug: str,
    stereotype: str | None = None,
    package: str | None = None,
    health: str | None = None,
    element_ids: list[int] | None = None,
    user_id: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Build a Cytoscape-compatible subgraph for filtered elements.

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :param stereotype: Optional stereotype filter.
    :param package: Optional package filter.
    :param health: Optional health filter.
    :param element_ids: Restrict to these PKs when set.
    :param user_id: Authenticated user PK for audit logs.
    :return: ``{"elements": [node data...], "edges": [edge data...]}``
    :raises ValueError: If model not found.
    """
    filters = BrowseFilters(stereotype=stereotype, package=package, health=health)
    ymodel = resolve_model(model_slug)
    qs = _filtered_queryset(ymodel, filters)
    if element_ids is not None:
        qs = qs.filter(pk__in=element_ids)
    elements = list(qs.select_related("stereotype", "package"))
    id_set = {el.pk for el in elements}
    nodes = [
        {
            "data": {
                "id": str(el.pk),
                "label": el.name,
                "stereotype": el.stereotype.name if el.stereotype_id else "",
            }
        }
        for el in elements
    ]
    rels = Relationship.objects.filter(model=ymodel, source_id__in=id_set, target_id__in=id_set)
    edges = [
        {
            "data": {
                "id": str(rel.pk),
                "source": str(rel.source_id),
                "target": str(rel.target_id),
                "label": rel.stereotype.slug if rel.stereotype_id else "rel",
            }
        }
        for rel in rels.select_related("stereotype")
    ]
    logger.info(
        "browse_service.subgraph_for_elements | exit model_slug=%s node_count=%s edge_count=%s user_id=%s",
        model_slug,
        len(nodes),
        len(edges),
        user_id,
    )
    return {"elements": nodes, "edges": edges}


def _filtered_queryset(ymodel: YggdrasilModel, filters: BrowseFilters) -> QuerySet[Element]:
    """Apply browse filters to an element queryset."""
    qs = Element.objects.filter(model=ymodel).select_related("stereotype", "package")
    if filters.stereotype:
        qs = qs.filter(
            Q(stereotype__slug__iexact=filters.stereotype)
            | Q(stereotype__name__iexact=filters.stereotype)
        )
    if filters.package:
        qs = qs.filter(
            Q(package__slug__iexact=filters.package) | Q(package__name__iexact=filters.package)
        )
    if filters.health:
        qs = qs.filter(health__iexact=filters.health)
    return qs
