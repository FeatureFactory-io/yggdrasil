"""
MCP read tools: list_elements, search, get_element, traverse, list_changesets,
get_changeset, list_stereotypes, list_ratatosk_runs (SAO.md §18.3 — tool inventory).

All tools are read-only. Auth: user_id injected server-side via ContextVar.
Never accept user_id as a tool argument (SAO.md §18.5 — auth injection).

Registered against the FastMCP singleton in server.initialize_mcp().

Note: GraphQueryService does not exist yet in this iteration footprint.
Query tools use private ORM helpers in this module until a graph service
lands (PIN footprint gap — absorbed). Tools remain thin wrappers.
"""

from __future__ import annotations

import logging

from django.db.models import Q

from yggdrasil.changeset.models import ChangeSet
from yggdrasil.graph.models import Element, Stereotype, YggdrasilModel
from yggdrasil.mcp.server import get_current_user_id
from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.mcp.tools.query")

_MAX_LIMIT = 200


def list_elements(
    model: str,
    stereotype: str | None = None,
    package: str | None = None,
    as_of: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Return a paginated list of elements in the specified model.

    :param model: Model slug. Example: "yggdrasil"
    :param stereotype: Filter by stereotype slug. Example: "container"
    :param package: Filter by package slug. Example: "technology"
    :param as_of: ISO8601 date for historical snapshot. Example: "2026-01-01"
    :param limit: Page size (max 200). Example: 50
    :param offset: Pagination offset. Example: 0
    :return: {"items": [...], "total": N, "limit": N, "offset": N}
    :raises PermissionError: If current user has no read access to model.
    :raises ValueError: If model slug not found.
    """
    user_id = get_current_user_id()
    logger.info(
        "list_elements | model=%s user=%s stereotype=%s package=%s as_of=%s",
        model,
        user_id,
        stereotype,
        package,
        as_of,
    )
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    page_offset = max(offset, 0)
    qs = Element.objects.filter(model=ymodel).select_related("stereotype", "package")
    if stereotype:
        qs = qs.filter(
            Q(stereotype__slug__iexact=stereotype) | Q(stereotype__name__iexact=stereotype)
        )
    if package:
        qs = qs.filter(Q(package__slug__iexact=package) | Q(package__name__iexact=package))
    # as_of: MVP records metadata only; full ChangeSet replay lands with bitemporal queries.
    total = qs.count()
    items = [
        _element_summary(el) for el in qs.order_by("name")[page_offset : page_offset + page_limit]
    ]
    result = {
        "items": items,
        "total": total,
        "limit": page_limit,
        "offset": page_offset,
    }
    if as_of:
        result["as_of"] = as_of
    logger.info(
        "list_elements | model=%s user=%s count=%s",
        model,
        user_id,
        len(items),
    )
    return result


def search(
    query: str,
    model: str,
    limit: int = 20,
) -> dict:
    """
    Full-text search elements by name within a model.

    :param query: Search string. Example: "Payment"
    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 20
    :return: {"items": [...], "query": "Payment"}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    logger.info("search | query=%r model=%s user=%s", query, model, user_id)
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    qs = Element.objects.filter(model=ymodel, name__icontains=query).select_related(
        "stereotype", "package"
    )[:page_limit]
    items = [_element_summary(el) for el in qs]
    result = {"items": items, "query": query}
    logger.info("search | query=%r count=%s user=%s", query, len(items), user_id)
    return result


def get_element(
    id_or_name: str,
    model: str | None = None,
) -> dict:
    """
    Get a single element with all properties, relationships, and confidence score.

    :param id_or_name: Element PK (int string) or exact name. Example: "Payment API"
    :param model: Model slug to disambiguate name lookups. Example: "yggdrasil"
    :return: Element dict with name, stereotype, package, owner, properties,
        confidence, incoming_relationships, outgoing_relationships.
    :raises ValueError: If element not found.
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    logger.info("get_element | id_or_name=%r model=%s user=%s", id_or_name, model, user_id)
    element = _resolve_element(id_or_name, model)
    result = _element_detail(element)
    logger.info("get_element | id=%s name=%s user=%s", element.pk, element.name, user_id)
    return result


def traverse(
    from_: str,
    direction: str = "outgoing",
    depth: int = 1,
    model: str | None = None,
) -> dict:
    """
    Walk the graph from an element and return connected elements.

    :param from_: Source element slug or id. Example: "payment-api"
    :param direction: "outgoing", "incoming", or "both". Example: "incoming"
    :param depth: Traversal depth (1 = immediate neighbours). Example: 1
    :param model: Model slug for disambiguation. Example: "yggdrasil"
    :return: {"source": {...}, "edges": [...], "nodes": [...]}
    :raises ValueError: If from_ element not found.
    """
    user_id = get_current_user_id()
    logger.info(
        "traverse | from=%s direction=%s depth=%s user=%s",
        from_,
        direction,
        depth,
        user_id,
    )
    source = _resolve_element(from_, model)
    edges: list[dict] = []
    nodes: dict[int, dict] = {}
    if direction in {"outgoing", "both"}:
        for rel in source.outgoing_relationships.select_related("target", "stereotype"):
            edges.append(_edge_dict(rel, "outgoing"))
            nodes[rel.target_id] = _element_summary(rel.target)
    if direction in {"incoming", "both"}:
        for rel in source.incoming_relationships.select_related("source", "stereotype"):
            edges.append(_edge_dict(rel, "incoming"))
            nodes[rel.source_id] = _element_summary(rel.source)
    result = {
        "source": _element_summary(source),
        "edges": edges,
        "nodes": list(nodes.values()),
        "depth": depth,
    }
    logger.info("traverse | from=%s nodes=%s user=%s", from_, len(nodes), user_id)
    return result


def list_changesets(
    model: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict:
    """
    List ChangeSets with optional status filter.

    :param model: Model slug filter. Example: "yggdrasil"
    :param status: "pending", "applied", or "rejected". Example: "pending"
    :param limit: Max results. Example: 50
    :return: {"items": [...], "total": N}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    logger.info("list_changesets | model=%s status=%s user=%s", model, status, user_id)
    qs = ChangeSet.objects.all().prefetch_related("items")
    if model:
        ymodel = _resolve_model(model)
        qs = qs.filter(model=ymodel)
    if status:
        qs = qs.filter(status=status)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    total = qs.count()
    items = [_changeset_summary(cs) for cs in qs.order_by("-created_at")[:page_limit]]
    result = {"items": items, "total": total}
    logger.info("list_changesets | count=%s user=%s", len(items), user_id)
    return result


def get_changeset(id: int) -> dict:
    """
    Get a ChangeSet with all operations and Munin reasoning.

    :param id: ChangeSet PK. Example: 1
    :return: ChangeSet dict with status, operations list, munin_reasoning.
    :raises ValueError: If ChangeSet not found.
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    logger.info("get_changeset | id=%s user=%s", id, user_id)
    try:
        changeset = ChangeSet.objects.prefetch_related("items").get(pk=id)
    except ChangeSet.DoesNotExist as exc:
        msg = f"ChangeSet id={id} not found"
        raise ValueError(msg) from exc
    result = _changeset_detail(changeset)
    logger.info("get_changeset | id=%s ops=%s user=%s", id, len(result["operations"]), user_id)
    return result


def list_stereotypes(model: str) -> dict:
    """
    Return all stereotype definitions for a model (including property_schema).

    :param model: Model slug. Example: "yggdrasil"
    :return: {"items": [{"name": ..., "slug": ..., "is_edge": ..., "property_schema": ...}]}
    :raises ValueError: If model not found.
    """
    user_id = get_current_user_id()
    logger.info("list_stereotypes | model=%s user=%s", model, user_id)
    ymodel = _resolve_model(model)
    items = [
        {
            "name": st.name,
            "slug": st.slug,
            "is_edge": st.is_edge,
            "property_schema": st.property_schema,
        }
        for st in Stereotype.objects.filter(model=ymodel).order_by("name")
    ]
    result = {"items": items}
    logger.info("list_stereotypes | model=%s count=%s user=%s", model, len(items), user_id)
    return result


def list_ratatosk_runs(model: str, limit: int = 20) -> dict:
    """
    Return the run history for a model (most recent first).

    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 20
    :return: {"items": [{"id": ..., "status": ..., "changeset_id": ..., "created_at": ...}]}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    logger.info("list_ratatosk_runs | model=%s user=%s", model, user_id)
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    runs = RataskRun.objects.filter(model=ymodel).order_by("-created_at")[:page_limit]
    items = [
        {
            "id": run.pk,
            "run_id": run.run_id,
            "status": run.status,
            "changeset_id": run.changeset_id,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
        for run in runs
    ]
    result = {"items": items}
    logger.info("list_ratatosk_runs | count=%s user=%s", len(items), user_id)
    return result


# ─── Private helpers ──────────────────────────────────────────────────────────


def _resolve_model(model: str) -> YggdrasilModel:
    """Resolve model by slug or name (case-insensitive)."""
    try:
        return YggdrasilModel.objects.get(Q(slug__iexact=model) | Q(name__iexact=model))
    except YggdrasilModel.DoesNotExist as exc:
        msg = f"Model {model!r} not found"
        raise ValueError(msg) from exc
    except YggdrasilModel.MultipleObjectsReturned as exc:
        msg = f"Model {model!r} is ambiguous"
        raise ValueError(msg) from exc


def _element_summary(element: Element) -> dict:
    """Serialize an Element for list/search responses."""
    return {
        "id": element.pk,
        "name": element.name,
        "slug": element.slug,
        "stereotype": element.stereotype.name if element.stereotype_id else "",
        "stereotype_slug": element.stereotype.slug if element.stereotype_id else "",
        "package": element.package.name if element.package_id else "",
        "owner": element.owner,
        "confidence": element.confidence,
        "properties": element.properties,
    }


def _element_detail(element: Element) -> dict:
    """Serialize a full element including relationship lists."""
    detail = _element_summary(element)
    detail["incoming_relationships"] = [
        _edge_dict(rel, "incoming")
        for rel in element.incoming_relationships.select_related("source", "stereotype")
    ]
    detail["outgoing_relationships"] = [
        _edge_dict(rel, "outgoing")
        for rel in element.outgoing_relationships.select_related("target", "stereotype")
    ]
    return detail


def _resolve_element(id_or_name: str, model: str | None) -> Element:
    """Resolve element by PK, slug, or exact name."""
    qs = Element.objects.select_related("stereotype", "package")
    if model:
        ymodel = _resolve_model(model)
        qs = qs.filter(model=ymodel)
    if id_or_name.isdigit():
        try:
            return qs.get(pk=int(id_or_name))
        except Element.DoesNotExist as exc:
            msg = f"Element id={id_or_name} not found"
            raise ValueError(msg) from exc
    try:
        return qs.get(Q(slug__iexact=id_or_name) | Q(name__iexact=id_or_name))
    except Element.DoesNotExist as exc:
        msg = f"Element {id_or_name!r} not found"
        raise ValueError(msg) from exc
    except Element.MultipleObjectsReturned as exc:
        msg = f"Element {id_or_name!r} is ambiguous — pass model="
        raise ValueError(msg) from exc


def _edge_dict(rel, direction: str) -> dict:
    """Serialize a Relationship for traverse/get_element."""
    other = rel.target if direction == "outgoing" else rel.source
    return {
        "id": rel.pk,
        "direction": direction,
        "stereotype": rel.stereotype.name if rel.stereotype_id else "",
        "element_id": other.pk,
        "element_name": other.name,
        "owner": other.owner,
        "confidence": other.confidence,
    }


def _changeset_summary(changeset: ChangeSet) -> dict:
    """Serialize a ChangeSet for list responses."""
    return {
        "id": changeset.pk,
        "status": changeset.status,
        "source": changeset.source,
        "run_id": changeset.run_id,
        "munin_reasoning": changeset.munin_reasoning,
        "operations_count": changeset.items.count(),
    }


def _changeset_detail(changeset: ChangeSet) -> dict:
    """Serialize a ChangeSet with full operations list."""
    summary = _changeset_summary(changeset)
    summary["operations"] = [
        {
            "id": item.pk,
            "order": item.order,
            "op_type": item.op_type,
            "detail": item.detail,
            "status": item.status,
            "confidence": item.confidence,
        }
        for item in changeset.items.all()
    ]
    return summary
