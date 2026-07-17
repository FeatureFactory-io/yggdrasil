"""
MCP read tools: list_elements, search, get_element, traverse, list_changesets,
get_changeset, list_stereotypes, list_ratatosk_runs (SAO.md §18.3 — tool inventory).

All tools are read-only. Auth: user_id injected server-side via ContextVar.
Never accept user_id as a tool argument (SAO.md §18.5 — auth injection).

Registered against the FastMCP singleton in server.initialize_mcp().
"""

from __future__ import annotations

import logging

logger = logging.getLogger("yggdrasil.mcp.tools.query")


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
    raise NotImplementedError()


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
    raise NotImplementedError()


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
    raise NotImplementedError()


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
    raise NotImplementedError()


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
    raise NotImplementedError()


def get_changeset(id: int) -> dict:
    """
    Get a ChangeSet with all operations and Munin reasoning.

    :param id: ChangeSet PK. Example: 1
    :return: ChangeSet dict with status, operations list, munin_reasoning.
    :raises ValueError: If ChangeSet not found.
    :raises PermissionError: If current user has no read access.
    """
    raise NotImplementedError()


def list_stereotypes(model: str) -> dict:
    """
    Return all stereotype definitions for a model (including property_schema).

    :param model: Model slug. Example: "yggdrasil"
    :return: {"items": [{"name": ..., "slug": ..., "is_edge": ..., "property_schema": ...}]}
    :raises ValueError: If model not found.
    """
    raise NotImplementedError()


def list_ratatosk_runs(model: str, limit: int = 20) -> dict:
    """
    Return the run history for a model (most recent first).

    :param model: Model slug. Example: "yggdrasil"
    :param limit: Max results. Example: 20
    :return: {"items": [{"id": ..., "status": ..., "changeset_id": ..., "created_at": ...}]}
    :raises PermissionError: If current user has no read access.
    """
    raise NotImplementedError()
