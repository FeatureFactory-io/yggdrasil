"""
Browse/query service for the View Browser and MCP read tools.

Shared ORM layer — web views and MCP tools call these functions; no MCP-specific
logic here (SAO §18.2 Case A Service Bridge).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from django.db.models import Q, QuerySet

from yggdrasil.graph.models import Element, Package, Relationship, Stereotype, YggdrasilModel

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger("yggdrasil.graph.browse")

MAX_LIMIT = 200
DEFAULT_MODEL_SLUG = "yggdrasil"
MODEL_COOKIE_NAME = "yggdrasil_model"
MAX_DEPTH = 20
DEFAULT_DEPTH = 1


@dataclass(frozen=True)
class BrowseFilters:
    """Filter parameters for element list and subgraph queries."""

    stereotype: str | None = None
    package: str | None = None
    health: str | None = None
    as_of: str | None = None
    packages: tuple[str, ...] = ()
    stereotypes: tuple[str, ...] = ()
    relationship_stereotypes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BrowseResult:
    """Paginated element list result."""

    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    as_of: str | None = None


@dataclass(frozen=True)
class DepthSubgraph:
    """Depth-scoped subgraph for View Browser and MCP traverse."""

    node_summaries: list[dict[str, Any]]
    cytoscape_elements: list[dict[str, Any]]
    cytoscape_edges: list[dict[str, Any]]
    max_depth: int
    parent_map: dict[int, int | None]
    root_ids: frozenset[int]


def list_readable_models(user: AbstractBaseUser) -> QuerySet[YggdrasilModel]:
    """
    Return Models the signed-in user may read for the View Browser switcher.

    Admin users (staff/superuser) see all Models. Other users see Models with
    no ``owner_group`` or whose ``owner_group`` matches one of the user's groups.

    :param user: Authenticated Django user.
    :return: Queryset ordered by ``name``.
    """
    logger.info("browse_service.list_readable_models | entry | user_pk=%s", user.pk)
    if user.is_superuser or user.is_staff:
        queryset = YggdrasilModel.objects.all()
    else:
        group_ids = list(user.groups.values_list("pk", flat=True))
        queryset = YggdrasilModel.objects.filter(
            Q(owner_group__isnull=True) | Q(owner_group_id__in=group_ids)
        )
    queryset = queryset.order_by("name")
    logger.info(
        "browse_service.list_readable_models | exit | user_pk=%s model_count=%s",
        user.pk,
        queryset.count(),
    )
    return queryset


def resolve_default_model_slug(
    user: AbstractBaseUser,
    cookie_value: str | None,
) -> str | None:
    """
    Resolve the default Model slug for unscoped ``GET /views/`` redirects.

    Priority: sole visible Model → valid cookie → first readable by ``name``.

    :param user: Authenticated Django user.
    :param cookie_value: Last-used Model slug from cookie, if any.
    :return: Default slug, or ``None`` when the user can read zero Models.
    """
    logger.info("browse_service.resolve_default_model_slug | entry | user_pk=%s", user.pk)
    readable = list(list_readable_models(user))
    if not readable:
        logger.info(
            "browse_service.resolve_default_model_slug | error | user_pk=%s reason=no_models",
            user.pk,
        )
        return None
    if len(readable) == 1:
        slug = readable[0].slug
        logger.info(
            "browse_service.resolve_default_model_slug | branch | user_pk=%s "
            "reason=sole_visible model_slug=%s",
            user.pk,
            slug,
        )
        return slug
    if cookie_value:
        for model in readable:
            if model.slug.lower() == cookie_value.lower():
                logger.info(
                    "browse_service.resolve_default_model_slug | branch | user_pk=%s "
                    "reason=cookie model_slug=%s",
                    user.pk,
                    model.slug,
                )
                return model.slug
    slug = readable[0].slug
    logger.info(
        "browse_service.resolve_default_model_slug | branch | user_pk=%s "
        "reason=first_by_name model_slug=%s",
        user.pk,
        slug,
    )
    return slug


def user_can_read_model(user: AbstractBaseUser, model_slug: str) -> YggdrasilModel:
    """
    Resolve a Model slug and verify the user may read it.

    :param user: Authenticated Django user.
    :param model_slug: Model slug from the URL. Example: ``"yggdrasil"``.
    :return: Matching ``YggdrasilModel``.
    :raises ValueError: If the slug does not exist.
    :raises PermissionError: If the user cannot read the Model.
    """
    model = resolve_model(model_slug)
    readable_slugs = {item.slug.lower() for item in list_readable_models(user)}
    if model.slug.lower() not in readable_slugs:
        msg = f"Model {model_slug!r} not readable"
        raise PermissionError(msg)
    return model


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
    Serialize an element for API/list[Any] responses.

    :param element: ORM element with stereotype/package loaded.
    :return: Summary dict[str, Any] including health and source.
    """
    return {
        "id": element.pk,
        "name": element.name,
        "slug": element.slug,
        "stereotype": element.stereotype.name if element.stereotype_id else "",
        "stereotype_slug": element.stereotype.slug if element.stereotype_id else "",
        "package": (element.package.name if element.package else ""),
        "package_slug": (element.package.slug if element.package else ""),
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
    :return: Template-friendly row dict[str, Any].
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
    Return a paginated, filterable element list[Any] for a model.

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
    relationship_stereotypes = [
        {"name": st.name, "slug": st.slug}
        for st in Stereotype.objects.filter(metamodel=ymodel.metamodel, is_edge=True).order_by(
            "name"
        )
    ]
    health = [{"value": value, "label": label} for value, label in Element.HEALTH_CHOICES]
    return {
        "packages": packages,
        "stereotypes": stereotypes,
        "relationship_stereotypes": relationship_stereotypes,
        "health": health,
    }


def build_package_scoped_filter_options(
    *,
    model_slug: str,
    packages: tuple[str, ...],
) -> dict[str, list[dict[str, str]]]:
    """
    Narrow stereotype filter options to elements in selected packages.

    :param model_slug: Model slug. Example: ``"yggdrasil"``.
    :param packages: Selected package slugs from active filters.
    :return: Filter options with scoped ``stereotypes`` and ``relationship_stereotypes``.
    :raises ValueError: If model not found.
    """
    base = list_filter_options(model_slug=model_slug)
    if not packages:
        return base
    ymodel = resolve_model(model_slug)
    pkg_slugs = {pkg.lower() for pkg in packages}
    scoped_elements = Element.objects.filter(
        model=ymodel,
        package__slug__in=pkg_slugs,
    ).select_related("stereotype")
    element_st_slugs = {el.stereotype.slug for el in scoped_elements if el.stereotype_id}
    element_ids = set(scoped_elements.values_list("pk", flat=True))
    rel_st_slugs = set(
        Relationship.objects.filter(model=ymodel)
        .filter(Q(source_id__in=element_ids) | Q(target_id__in=element_ids))
        .exclude(stereotype__isnull=True)
        .values_list("stereotype__slug", flat=True)
    )
    stereotypes = [st for st in base["stereotypes"] if st["slug"] in element_st_slugs]
    relationship_stereotypes = [
        st for st in base["relationship_stereotypes"] if st["slug"] in rel_st_slugs
    ]
    logger.info(
        "browse_service.build_package_scoped_filter_options | exit | model_slug=%s "
        "packages=%s element_stereotypes=%s rel_stereotypes=%s",
        model_slug,
        len(packages),
        len(stereotypes),
        len(relationship_stereotypes),
    )
    return {
        **base,
        "stereotypes": stereotypes,
        "relationship_stereotypes": relationship_stereotypes,
    }


def _has_narrowing_filter(filters: BrowseFilters) -> bool:
    """Return True when any element-narrowing browse filter is active."""
    return bool(
        filters.stereotype
        or filters.package
        or filters.health
        or filters.packages
        or filters.stereotypes
    )


def resolve_root_element_ids(ymodel: YggdrasilModel, filters: BrowseFilters) -> set[int]:
    """
    Resolve BFS root element PKs from browse filters.

    When no element-narrowing filter is active, roots are graph sources
    (nodes with zero incoming edges).

    :param ymodel: Target model instance.
    :param filters: Active browse filters.
    :return: Set of root element primary keys.
    """
    logger.info(
        "browse_service.resolve_root_element_ids | entry | model_slug=%s filters=%s",
        ymodel.slug,
        filters,
    )
    if _has_narrowing_filter(filters):
        root_ids = set(_filtered_queryset(ymodel, filters).values_list("pk", flat=True))
    else:
        incoming_targets = set(
            Relationship.objects.filter(model=ymodel).values_list("target_id", flat=True)
        )
        root_ids = set(
            Element.objects.filter(model=ymodel)
            .exclude(pk__in=incoming_targets)
            .values_list("pk", flat=True)
        )
        logger.info(
            "browse_service.resolve_root_element_ids | branch | reason=graph_sources root_count=%s",
            len(root_ids),
        )
    logger.info(
        "browse_service.resolve_root_element_ids | exit | model_slug=%s root_count=%s",
        ymodel.slug,
        len(root_ids),
    )
    return root_ids


def _outgoing_adjacency(ymodel: YggdrasilModel) -> dict[int, list[int]]:
    """Build source_id -> [target_id, ...] adjacency for a model."""
    adjacency: dict[int, list[int]] = defaultdict(list)
    for source_id, target_id in Relationship.objects.filter(model=ymodel).values_list(
        "source_id", "target_id"
    ):
        adjacency[source_id].append(target_id)
    return adjacency


def _incoming_adjacency(ymodel: YggdrasilModel) -> dict[int, list[int]]:
    """Build target_id -> [source_id, ...] adjacency for a model."""
    adjacency: dict[int, list[int]] = defaultdict(list)
    for source_id, target_id in Relationship.objects.filter(model=ymodel).values_list(
        "source_id", "target_id"
    ):
        adjacency[target_id].append(source_id)
    return adjacency


def _bfs_expand(
    root_ids: set[int],
    adjacency: dict[int, list[int]],
    depth: int,
) -> tuple[set[int], dict[int, int | None]]:
    """
    Expand ``depth - 1`` hops along adjacency from ``root_ids``.

    :param root_ids: Starting element PKs.
    :param adjacency: Directed adjacency list.
    :param depth: Level count (1 = roots only).
    :return: Visited PKs and parent map (root -> None).
    """
    visited = set(root_ids)
    parent_map: dict[int, int | None] = dict.fromkeys(root_ids, None)
    frontier = set(root_ids)
    for _ in range(max(depth - 1, 0)):
        if not frontier:
            break
        next_frontier: set[int] = set()
        for node_id in frontier:
            for neighbor_id in adjacency.get(node_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    parent_map[neighbor_id] = node_id
                    next_frontier.add(neighbor_id)
        frontier = next_frontier
    return visited, parent_map


def compute_max_depth(ymodel: YggdrasilModel, root_ids: set[int]) -> int:
    """
    Compute longest reachable outgoing hop depth from roots (capped at ``MAX_DEPTH``).

    :param ymodel: Target model instance.
    :param root_ids: BFS root element PKs.
    :return: Maximum useful depth level (at least 1).
    """
    if not root_ids:
        return 1
    adjacency = _outgoing_adjacency(ymodel)
    depth = 1
    frontier = set(root_ids)
    visited = set(root_ids)
    while frontier and depth < MAX_DEPTH:
        next_frontier: set[int] = set()
        for node_id in frontier:
            for neighbor_id in adjacency.get(node_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    next_frontier.add(neighbor_id)
        if not next_frontier:
            break
        depth += 1
        frontier = next_frontier
    capped = depth >= MAX_DEPTH
    logger.info(
        "browse_service.compute_max_depth | exit | max_depth=%s capped=%s",
        depth,
        capped,
    )
    return depth


def subgraph_from_roots(
    *,
    model_slug: str,
    stereotype: str | None = None,
    package: str | None = None,
    health: str | None = None,
    packages: tuple[str, ...] = (),
    stereotypes: tuple[str, ...] = (),
    relationship_stereotypes: tuple[str, ...] = (),
    depth: int = DEFAULT_DEPTH,
    user_id: int | None = None,
    field_map: dict[str, list[str]] | None = None,
) -> DepthSubgraph:
    """
    Build a depth-scoped subgraph from filter roots via outgoing BFS.

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :param stereotype: Optional stereotype filter for roots.
    :param package: Optional package filter for roots.
    :param health: Optional health filter for roots.
    :param depth: Level count (1 = roots only). Example: ``2``
    :param user_id: Authenticated user PK for audit logs.
    :return: ``DepthSubgraph`` with summaries, cytoscape payload, and tree metadata.
    :raises ValueError: If model not found or depth invalid.
    """
    if depth < 1:
        logger.info(
            "browse_service.subgraph_from_roots | error | depth=%s reason=invalid",
            depth,
        )
        msg = f"depth must be >= 1, got {depth}"
        raise ValueError(msg)
    filters = BrowseFilters(
        stereotype=stereotype,
        package=package,
        health=health,
        packages=packages,
        stereotypes=stereotypes,
        relationship_stereotypes=relationship_stereotypes,
    )
    field_map = field_map or {}
    logger.info(
        "browse_service.subgraph_from_roots | entry | model_slug=%s depth=%s direction=outgoing user_id=%s",
        model_slug,
        depth,
        user_id,
    )
    ymodel = resolve_model(model_slug)
    root_ids = resolve_root_element_ids(ymodel, filters)
    adjacency = _outgoing_adjacency(ymodel)
    visited, parent_map = _bfs_expand(root_ids, adjacency, depth)
    elements = list(
        Element.objects.filter(model=ymodel, pk__in=visited).select_related("stereotype", "package")
    )
    id_set = {el.pk for el in elements}
    node_summaries = [element_summary(el) for el in sorted(elements, key=lambda e: e.name)]
    summary_by_id = {str(summary["id"]): summary for summary in node_summaries}
    cytoscape_elements = []
    for el in elements:
        summary = summary_by_id[str(el.pk)]
        label = el.name
        if field_map:
            from yggdrasil.graph import browse_content

            paths = browse_content.field_map_for_element(summary, field_map)
            label = browse_content.format_node_label_from_paths(summary, paths)
        cytoscape_elements.append(
            {
                "data": {
                    "id": str(el.pk),
                    "label": label,
                    "stereotype": el.stereotype.name if el.stereotype_id else "",
                }
            }
        )
    rels = Relationship.objects.filter(
        model=ymodel, source_id__in=id_set, target_id__in=id_set
    ).select_related("stereotype")
    if relationship_stereotypes:
        rels = rels.filter(stereotype__slug__in=[s.lower() for s in relationship_stereotypes])
    cytoscape_edges = [
        {
            "data": {
                "id": str(rel.pk),
                "source": str(rel.source_id),
                "target": str(rel.target_id),
                "label": rel.stereotype.slug if rel.stereotype_id else "rel",
            }
        }
        for rel in rels
    ]
    max_depth = compute_max_depth(ymodel, root_ids)
    logger.info(
        "browse_service.subgraph_from_roots | processing | node_count=%s edge_count=%s",
        len(node_summaries),
        len(cytoscape_edges),
    )
    logger.info(
        "browse_service.subgraph_from_roots | exit | model_slug=%s max_depth=%s user_id=%s",
        model_slug,
        max_depth,
        user_id,
    )
    return DepthSubgraph(
        node_summaries=node_summaries,
        cytoscape_elements=cytoscape_elements,
        cytoscape_edges=cytoscape_edges,
        max_depth=max_depth,
        parent_map=parent_map,
        root_ids=frozenset(root_ids),
    )


def bfs_from_element(
    element: Element,
    *,
    direction: str = "outgoing",
    depth: int = DEFAULT_DEPTH,
) -> DepthSubgraph:
    """
    Multi-hop BFS from a single element (MCP ``traverse``).

    Uses the same level semantics as ``subgraph_from_roots``: depth=1 is the
    source only; depth=2 adds immediate neighbors in ``direction``.

    :param element: Source element ORM instance.
    :param direction: ``outgoing``, ``incoming``, or ``both``.
    :param depth: Level count including the source. Example: ``2``
    :return: ``DepthSubgraph`` scoped to the walk.
    :raises ValueError: If depth or direction is invalid.
    """
    if depth < 1:
        msg = f"depth must be >= 1, got {depth}"
        raise ValueError(msg)
    if direction not in {"outgoing", "incoming", "both"}:
        msg = f"direction must be outgoing, incoming, or both, got {direction!r}"
        raise ValueError(msg)
    ymodel = element.model
    root_ids = {element.pk}
    if direction == "outgoing":
        adjacency = _outgoing_adjacency(ymodel)
    elif direction == "incoming":
        adjacency = _incoming_adjacency(ymodel)
    else:
        outgoing = _outgoing_adjacency(ymodel)
        incoming = _incoming_adjacency(ymodel)
        merged: dict[int, list[int]] = defaultdict(list)
        for node_id, neighbors in outgoing.items():
            merged[node_id].extend(neighbors)
        for node_id, neighbors in incoming.items():
            merged[node_id].extend(neighbors)
        adjacency = merged
    visited, parent_map = _bfs_expand(root_ids, adjacency, depth)
    elements = list(
        Element.objects.filter(model=ymodel, pk__in=visited).select_related("stereotype", "package")
    )
    id_set = {el.pk for el in elements}
    node_summaries = [element_summary(el) for el in sorted(elements, key=lambda e: e.name)]
    cytoscape_elements = [
        {
            "data": {
                "id": str(el.pk),
                "label": el.name,
                "stereotype": el.stereotype.name if el.stereotype_id else "",
            }
        }
        for el in elements
    ]
    rels = Relationship.objects.filter(
        model=ymodel, source_id__in=id_set, target_id__in=id_set
    ).select_related("stereotype")
    cytoscape_edges = [
        {
            "data": {
                "id": str(rel.pk),
                "source": str(rel.source_id),
                "target": str(rel.target_id),
                "label": rel.stereotype.slug if rel.stereotype_id else "rel",
            }
        }
        for rel in rels
    ]
    max_depth = compute_max_depth(ymodel, root_ids)
    return DepthSubgraph(
        node_summaries=node_summaries,
        cytoscape_elements=cytoscape_elements,
        cytoscape_edges=cytoscape_edges,
        max_depth=max_depth,
        parent_map=parent_map,
        root_ids=frozenset(root_ids),
    )


def subgraph_for_elements(
    *,
    model_slug: str,
    stereotype: str | None = None,
    package: str | None = None,
    health: str | None = None,
    packages: tuple[str, ...] = (),
    stereotypes: tuple[str, ...] = (),
    relationship_stereotypes: tuple[str, ...] = (),
    element_ids: list[int] | None = None,
    depth: int = DEFAULT_DEPTH,
    user_id: int | None = None,
    field_map: dict[str, list[str]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Build a Cytoscape-compatible subgraph for filtered elements.

    :param model_slug: Model slug. Example: ``"yggdrasil"``
    :param stereotype: Optional stereotype filter.
    :param package: Optional package filter.
    :param health: Optional health filter.
    :param element_ids: Restrict to these PKs when set (legacy; prefer depth BFS).
    :param depth: Outgoing BFS level count from filter roots. Example: ``1``
    :param user_id: Authenticated user PK for audit logs.
    :return: ``{"elements": [node data...], "edges": [edge data...]}``
    :raises ValueError: If model not found.
    """
    if element_ids is not None:
        ymodel = resolve_model(model_slug)
        elements = list(
            Element.objects.filter(model=ymodel, pk__in=element_ids).select_related(
                "stereotype", "package"
            )
        )
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

    scoped = subgraph_from_roots(
        model_slug=model_slug,
        stereotype=stereotype,
        package=package,
        health=health,
        packages=packages,
        stereotypes=stereotypes,
        relationship_stereotypes=relationship_stereotypes,
        depth=depth,
        user_id=user_id,
        field_map=field_map,
    )
    logger.info(
        "browse_service.subgraph_for_elements | exit model_slug=%s node_count=%s edge_count=%s user_id=%s",
        model_slug,
        len(scoped.cytoscape_elements),
        len(scoped.cytoscape_edges),
        user_id,
    )
    return {"elements": scoped.cytoscape_elements, "edges": scoped.cytoscape_edges}


def get_element_for_inspector(element_id: int, *, user_id: int | None = None) -> dict[str, Any]:
    """
    Build inspector context for a single element and its connected relationships.

    :param element_id: Element primary key.
    :param user_id: Authenticated user PK for audit logs.
    :return: ``{"element": {...}, "relationships": [...]}``.
    :raises Element.DoesNotExist: If the element is missing.
    """
    element = Element.objects.select_related("stereotype", "package", "model").get(pk=element_id)
    outgoing = Relationship.objects.filter(source=element).select_related(
        "target", "stereotype", "source"
    )
    incoming = Relationship.objects.filter(target=element).select_related(
        "source", "stereotype", "target"
    )
    relationships: list[dict[str, Any]] = []
    for rel in outgoing:
        relationships.append(_connected_relationship_row(rel, element.pk, outbound=True))
    for rel in incoming:
        relationships.append(_connected_relationship_row(rel, element.pk, outbound=False))
    relationships.sort(key=lambda row: (row["edge_stereotype"], row["other_name"]))
    logger.info(
        "browse_service.get_element_for_inspector | exit element_id=%s rel_count=%s user_id=%s",
        element_id,
        len(relationships),
        user_id,
    )
    return {
        "element": element_summary(element),
        "relationships": relationships,
        "relationships_in": incoming.count(),
        "relationships_out": outgoing.count(),
    }


def get_relationship_for_inspector(
    relationship_id: int, *, user_id: int | None = None
) -> dict[str, Any]:
    """
    Build inspector context for a single relationship.

    :param relationship_id: Relationship primary key.
    :param user_id: Authenticated user PK for audit logs.
    :return: Relationship detail dict[str, Any] with endpoint element names.
    :raises Relationship.DoesNotExist: If the relationship is missing.
    """
    rel = Relationship.objects.select_related(
        "stereotype", "source", "target", "source__stereotype", "target__stereotype"
    ).get(pk=relationship_id)
    logger.info(
        "browse_service.get_relationship_for_inspector | exit relationship_id=%s user_id=%s",
        relationship_id,
        user_id,
    )
    return _relationship_inspector_detail(rel)


def _connected_relationship_row(
    rel: Relationship,
    element_id: int,
    *,
    outbound: bool,
) -> dict[str, Any]:
    """Map a relationship to an inspector connected-row dict."""
    other = rel.target if outbound else rel.source
    return {
        "id": rel.pk,
        "edge_stereotype": rel.stereotype.slug if rel.stereotype_id else "rel",
        "other_id": other.pk,
        "other_name": other.name,
        "outbound": outbound,
    }


def _relationship_inspector_detail(rel: Relationship) -> dict[str, Any]:
    """Serialize a relationship for the inspector partial."""
    return {
        "id": rel.pk,
        "from_id": rel.source_id,
        "to_id": rel.target_id,
        "from_element": rel.source.name,
        "to_element": rel.target.name,
        "edge_stereotype": rel.stereotype.slug if rel.stereotype_id else "rel",
        "confidence": rel.confidence,
        "properties": rel.properties,
    }


def _filtered_queryset(ymodel: YggdrasilModel, filters: BrowseFilters) -> QuerySet[Element]:
    """Apply browse filters to an element queryset."""
    qs = Element.objects.filter(model=ymodel).select_related("stereotype", "package")
    if filters.packages:
        slugs = [pkg.lower() for pkg in filters.packages]
        qs = qs.filter(Q(package__slug__in=slugs) | Q(package__name__in=slugs))
    elif filters.package:
        qs = qs.filter(
            Q(package__slug__iexact=filters.package) | Q(package__name__iexact=filters.package)
        )
    if filters.stereotypes:
        slugs = [st.lower() for st in filters.stereotypes]
        qs = qs.filter(Q(stereotype__slug__in=slugs) | Q(stereotype__name__in=slugs))
    elif filters.stereotype:
        qs = qs.filter(
            Q(stereotype__slug__iexact=filters.stereotype)
            | Q(stereotype__name__iexact=filters.stereotype)
        )
    if filters.health:
        qs = qs.filter(health__iexact=filters.health)
    return qs
