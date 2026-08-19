"""
MCP read tools: list_elements, search, get_element, traverse, list_changesets,
get_changeset, list_stereotypes, list_ratatosk_runs (SAO.md §18.3 — tool inventory).

All tools are read-only. Auth: user_id injected server-side via ContextVar.
Never accept user_id as a tool argument (SAO.md §18.5 — auth injection).

Registered against the FastMCP singleton in server.initialize_mcp().

Note: Query tools delegate element listing to ``browse_service`` (Act 2).
Other helpers remain in this module until further extraction.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Q

from yggdrasil.changeset.models import ChangeSet
from yggdrasil.graph import browse_service
from yggdrasil.graph.models import Element, Package, Relationship, Stereotype, YggdrasilModel
from yggdrasil.mcp.server import get_current_user_id
from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.mcp.tools.query")

_MAX_LIMIT = 200


def _log(where: str, beat: str, **fields: object) -> None:
    """Emit a grep-friendly MCP query-tool story beat."""
    extras = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("%s | %s | %s", where, beat, extras)


def list_elements(
    model: str,
    stereotype: str | None = None,
    package: str | None = None,
    as_of: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Return a paginated list[Any] of elements in the specified model.

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
    _log(
        "list_elements",
        "entry",
        model=model,
        user=user_id,
        stereotype=stereotype,
        package=package,
        as_of=as_of,
        limit=limit,
        offset=offset,
    )
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    page_offset = max(offset, 0)
    _log(
        "list_elements",
        "validation",
        requested_limit=limit,
        page_limit=page_limit,
        capped=limit != page_limit,
    )
    result = browse_service.list_elements(
        model_slug=ymodel.slug,
        stereotype=stereotype,
        package=package,
        health=None,
        as_of=as_of,
        limit=page_limit,
        offset=page_offset,
        user_id=user_id,
    )
    payload: dict[str, Any] = {
        "items": result.items,
        "total": result.total,
        "limit": result.limit,
        "offset": result.offset,
    }
    if result.as_of:
        payload["as_of"] = result.as_of
    _log(
        "list_elements",
        "processing",
        total=result.total,
        returned=len(result.items),
    )
    _log(
        "list_elements",
        "exit",
        model=model,
        user=user_id,
        count=len(result.items),
    )
    return payload


def search(
    query: str,
    model: str,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Full-text search elements by name within a model.

    :param query: Search string. Example: "Payment"
    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 20
    :return: {"items": [...], "query": "Payment"}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    _log("search", "entry", query=query, model=model, user=user_id, limit=limit)
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    qs = Element.objects.filter(model=ymodel, name__icontains=query).select_related(
        "stereotype", "package"
    )[:page_limit]
    items = [_element_summary(el) for el in qs]
    result = {"items": items, "query": query}
    _log("search", "processing", matched=len(items), page_limit=page_limit)
    _log("search", "exit", query=query, count=len(items), user=user_id)
    return result


def get_element(
    id_or_name: str,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Get a single element with all properties, relationships, and confidence score.

    :param id_or_name: Element PK (int string) or exact name. Example: "Payment API"
    :param model: Model slug to disambiguate name lookups. Example: "yggdrasil"
    :return: Element dict[str, Any] with name, stereotype, package, owner, properties,
        confidence, incoming_relationships, outgoing_relationships.
    :raises ValueError: If element not found.
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    _log("get_element", "entry", id_or_name=id_or_name, model=model, user=user_id)
    element = _resolve_element(id_or_name, model)
    result = _element_detail(element)
    incoming = len(result.get("incoming_relationships") or [])
    outgoing = len(result.get("outgoing_relationships") or [])
    _log(
        "get_element",
        "processing",
        element_id=element.pk,
        incoming=incoming,
        outgoing=outgoing,
    )
    _log("get_element", "exit", id=element.pk, name=element.name, user=user_id)
    return result


def traverse(
    from_: str,
    direction: str = "outgoing",
    depth: int = 2,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Walk the graph from an element and return connected elements.

    :param from_: Source element slug or id. Example: ``"payment-api"``
    :param direction: ``outgoing``, ``incoming``, or ``both``. Example: ``"incoming"``
    :param depth: Level count including source (2 = source + one hop). Example: ``2``
    :param model: Model slug for disambiguation. Example: ``"yggdrasil"``
    :return: ``{"source": {...}, "edges": [...], "nodes": [...]}``
    :raises ValueError: If from_ element not found or depth invalid.
    """
    user_id = get_current_user_id()
    _log(
        "traverse",
        "entry",
        **{"from": from_, "direction": direction, "depth": depth, "model": model, "user": user_id},
    )
    source = _resolve_element(from_, model)
    scoped = browse_service.bfs_from_element(source, direction=direction, depth=depth)
    rel_ids = [int(edge["data"]["id"]) for edge in scoped.cytoscape_edges]
    rels = Relationship.objects.filter(pk__in=rel_ids).select_related(
        "source", "target", "stereotype"
    )
    edges: list[dict[str, Any]] = []
    for rel in rels:
        if rel.source_id == source.pk:
            edges.append(_edge_dict(rel, "outgoing"))
        elif rel.target_id == source.pk or direction == "incoming":
            edges.append(_edge_dict(rel, "incoming"))
        else:
            edges.append(_edge_dict(rel, "outgoing"))
    nodes = [summary for summary in scoped.node_summaries if summary["id"] != source.pk]
    result = {
        "source": _element_summary(source),
        "edges": edges,
        "nodes": nodes,
        "depth": depth,
    }
    _log(
        "traverse",
        "processing",
        visited=len(scoped.node_summaries),
        edge_count=len(edges),
    )
    _log("traverse", "exit", **{"from": from_, "node_count": len(nodes), "user": user_id})
    return result


def list_changesets(
    model: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """
    List ChangeSets with optional status filter.

    :param model: Model slug filter. Example: "yggdrasil"
    :param status: "pending", "applied", or "rejected". Example: "pending"
    :param limit: Max results. Example: 50
    :return: {"items": [...], "total": N}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    _log("list_changesets", "entry", model=model, status=status, user=user_id, limit=limit)
    qs = ChangeSet.objects.all().prefetch_related("items")
    if model:
        ymodel = _resolve_model(model)
        qs = qs.filter(model=ymodel)
        _log("list_changesets", "branch", reason="model_filter", model=model)
    else:
        _log("list_changesets", "branch", reason="all_models")
    if status:
        qs = qs.filter(status=status)
        _log("list_changesets", "branch", reason="status_filter", status=status)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    total = qs.count()
    items = [_changeset_summary(cs) for cs in qs.order_by("-created_at")[:page_limit]]
    result = {"items": items, "total": total}
    _log("list_changesets", "processing", total=total, returned=len(items))
    _log("list_changesets", "exit", count=len(items), user=user_id)
    return result


def get_changeset(id: int) -> dict[str, Any]:
    """
    Get a ChangeSet with all operations and Munin reasoning.

    :param id: ChangeSet PK. Example: 1
    :return: ChangeSet dict[str, Any] with status, operations list[Any], munin_reasoning.
    :raises ValueError: If ChangeSet not found.
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    _log("get_changeset", "entry", id=id, user=user_id)
    try:
        changeset = ChangeSet.objects.prefetch_related("items").get(pk=id)
    except ChangeSet.DoesNotExist as exc:
        _log("get_changeset", "error", id=id, reason="not_found")
        msg = f"ChangeSet id={id} not found"
        raise ValueError(msg) from exc
    result = _changeset_detail(changeset)
    _log("get_changeset", "processing", ops=len(result["operations"]), status=changeset.status)
    _log("get_changeset", "exit", id=id, ops=len(result["operations"]), user=user_id)
    return result


def list_stereotypes(model: str) -> dict[str, Any]:
    """
    Return all stereotype definitions for a model (including property_schema).

    :param model: Model slug. Example: "yggdrasil"
    :return: {"items": [{"name": ..., "slug": ..., "is_edge": ..., "property_schema": ...}]}
    :raises ValueError: If model not found.
    """
    user_id = get_current_user_id()
    _log("list_stereotypes", "entry", model=model, user=user_id)
    ymodel = _resolve_model(model)
    items = [
        {
            "name": st.name,
            "slug": st.slug,
            "is_edge": st.is_edge,
            "description": st.description,
            "property_schema": st.property_schema,
            "allowed_edge_rules": st.allowed_edge_rules,
        }
        for st in Stereotype.objects.filter(metamodel=ymodel.metamodel).order_by("name")
    ]
    result = {"items": items}
    _log("list_stereotypes", "processing", count=len(items))
    _log("list_stereotypes", "exit", model=model, count=len(items), user=user_id)
    return result


def list_packages(
    model: str,
    limit: int = 50,
) -> dict[str, Any]:
    """
    Return packages defined on the model's metamodel.

    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 50
    :return: {"items": [...], "total": N}
    :raises ValueError: If model slug not found.
    """
    user_id = get_current_user_id()
    _log("list_packages", "entry", model=model, user=user_id, limit=limit)
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    qs = Package.objects.filter(metamodel=ymodel.metamodel).order_by("name")[:page_limit]
    items = [
        {"name": pkg.name, "slug": pkg.slug, "description": pkg.description or ""} for pkg in qs
    ]
    result = {"items": items, "total": Package.objects.filter(metamodel=ymodel.metamodel).count()}
    _log("list_packages", "processing", total=result["total"], returned=len(items))
    _log("list_packages", "exit", model=model, count=len(items), user=user_id)
    return result


def list_relationships(
    model: str,
    stereotype: str | None = None,
    from_id: int | None = None,
    to_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """
    Return a paginated list[Any] of relationships in the specified model.

    :param model: Model slug. Example: "yggdrasil"
    :param stereotype: Filter by edge stereotype slug. Example: "depends_on"
    :param from_id: Filter by source element PK. Example: 1
    :param to_id: Filter by target element PK. Example: 2
    :param limit: Page size (max 200). Example: 50
    :param offset: Pagination offset. Example: 0
    :return: {"items": [...], "total": N, "limit": N, "offset": N}
    :raises ValueError: If model slug not found.
    """
    user_id = get_current_user_id()
    _log(
        "list_relationships",
        "entry",
        model=model,
        user=user_id,
        stereotype=stereotype,
        from_id=from_id,
        to_id=to_id,
        limit=limit,
        offset=offset,
    )
    ymodel = _resolve_model(model)
    page_limit = min(max(limit, 1), _MAX_LIMIT)
    page_offset = max(offset, 0)
    qs = Relationship.objects.filter(model=ymodel).select_related("source", "target", "stereotype")
    if stereotype or from_id is not None or to_id is not None:
        _log(
            "list_relationships",
            "branch",
            reason="filtered",
            stereotype=stereotype,
            from_id=from_id,
            to_id=to_id,
        )
    else:
        _log("list_relationships", "branch", reason="unfiltered")
    if stereotype:
        qs = qs.filter(
            Q(stereotype__slug__iexact=stereotype) | Q(stereotype__name__iexact=stereotype)
        )
    if from_id is not None:
        qs = qs.filter(source_id=from_id)
    if to_id is not None:
        qs = qs.filter(target_id=to_id)
    total = qs.count()
    items = [
        {
            "id": rel.pk,
            "source_id": rel.source_id,
            "target_id": rel.target_id,
            "source_name": rel.source.name,
            "target_name": rel.target.name,
            "stereotype": rel.stereotype.name if rel.stereotype_id else "",
            "stereotype_slug": rel.stereotype.slug if rel.stereotype_id else "",
        }
        for rel in qs.order_by("id")[page_offset : page_offset + page_limit]
    ]
    result = {
        "items": items,
        "total": total,
        "limit": page_limit,
        "offset": page_offset,
    }
    _log("list_relationships", "processing", total=total, returned=len(items))
    _log(
        "list_relationships",
        "exit",
        model=model,
        user=user_id,
        count=len(items),
        total=total,
    )
    return result


def list_ratatosk_runs(model: str, limit: int = 20) -> dict[str, Any]:
    """
    Return the run history for a model (most recent first).

    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 20
    :return: {"items": [{"id": ..., "status": ..., "changeset_id": ..., "created_at": ...}]}
    :raises PermissionError: If current user has no read access.
    """
    user_id = get_current_user_id()
    _log("list_ratatosk_runs", "entry", model=model, user=user_id, limit=limit)
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
    _log("list_ratatosk_runs", "processing", returned=len(items))
    _log("list_ratatosk_runs", "exit", count=len(items), user=user_id)
    return result


# ─── Private helpers ──────────────────────────────────────────────────────────


def _resolve_model(model: str) -> YggdrasilModel:
    """Resolve model by slug or name (case-insensitive)."""
    return browse_service.resolve_model(model)


def _element_summary(element: Element) -> dict[str, Any]:
    """Serialize an Element for list/search responses."""
    return browse_service.element_summary(element)


def _element_detail(element: Element) -> dict[str, Any]:
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
            _log("query._resolve_element", "error", id_or_name=id_or_name, reason="not_found")
            msg = f"Element id={id_or_name} not found"
            raise ValueError(msg) from exc
    try:
        return qs.get(Q(slug__iexact=id_or_name) | Q(name__iexact=id_or_name))
    except Element.DoesNotExist as exc:
        _log("query._resolve_element", "error", id_or_name=id_or_name, reason="not_found")
        msg = f"Element {id_or_name!r} not found"
        raise ValueError(msg) from exc
    except Element.MultipleObjectsReturned as exc:
        _log("query._resolve_element", "error", id_or_name=id_or_name, reason="ambiguous")
        msg = f"Element {id_or_name!r} is ambiguous — pass model="
        raise ValueError(msg) from exc


def _edge_dict(rel: Any, direction: str) -> dict[str, Any]:
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


def _changeset_summary(changeset: ChangeSet) -> dict[str, Any]:
    """Serialize a ChangeSet for list responses."""
    return {
        "id": changeset.pk,
        "status": changeset.status,
        "source": changeset.source,
        "run_id": changeset.run_id,
        "munin_reasoning": changeset.munin_reasoning,
        "operations_count": changeset.items.count(),
    }


def _changeset_detail(changeset: ChangeSet) -> dict[str, Any]:
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
