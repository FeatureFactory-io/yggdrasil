"""
MCP write tools: create_element, update_element, delete_element,
create_relationship, update_relationships_batch, set_model_mode (SAO.md §18.3).

All writes go through the Munin/ChangeSet pipeline — never direct ORM.
HITL gate: delete_element and delete_relationship always queue for human review.
Auth: user_id injected server-side via ContextVar — never from tool args.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("yggdrasil.mcp.tools.write")


def create_element(
    name: str,
    stereotype: str,
    model: str,
    package: str | None = None,
    owner: str = "",
    properties: dict | None = None,
) -> dict:
    """
    Propose adding a new element via the Munin/ChangeSet pipeline.

    In auto-approval mode the element is applied immediately.
    In manual-review mode a pending ChangeSet is returned.

    :param name: Element name. Example: "Notification Service"
    :param stereotype: Stereotype slug. Example: "container"
    :param model: Model slug. Example: "yggdrasil"
    :param package: Package slug. Example: "technology"
    :param owner: Owner team. Example: "payments-team"
    :param properties: Stereotype-driven attributes dict. Example: {"framework": "FastAPI"}
    :return: {"changeset_id": N, "status": "applied"|"pending", "operation": {...}}
    :raises PermissionError: If current user token has read-only scope.
    :raises ValueError: If stereotype or model not found.
    """
    raise NotImplementedError()


def update_element(
    id: int,
    model: str | None = None,
    **fields,
) -> dict:
    """
    Propose updating specific fields of an existing element.

    Only provided fields are changed. Produces an Update Element operation
    with a before/after diff in the ChangeSet detail.

    :param id: Element PK. Example: 3
    :param model: Model slug for validation. Example: "yggdrasil"
    :param fields: Fields to update (name, owner, package, properties).
        Example: owner="fulfillment-team"
    :return: {"changeset_id": N, "status": ..., "operation": {...}}
    :raises PermissionError: If current user token has read-only scope.
    :raises ValueError: If element not found.
    """
    raise NotImplementedError()


def delete_element(id: int, model: str | None = None) -> dict:
    """
    Propose deleting an element after Munin checks blast-radius.

    Always queued for human review (HITL gate — SAO.md §18.3).
    Munin reports the blast-radius (number of affected relationships).

    :param id: Element PK. Example: 1
    :param model: Model slug for validation. Example: "yggdrasil"
    :return: {"changeset_id": N, "status": "pending", "blast_radius": N}
    :raises PermissionError: If read-only scope.
    :raises ValueError: If element not found.
    """
    raise NotImplementedError()


def create_relationship(
    from_id: int,
    stereotype: str,
    to_id: int,
    model: str | None = None,
    properties: dict | None = None,
) -> dict:
    """
    Propose adding a new relationship via Munin after edge-rule validation.

    :param from_id: Source element PK. Example: 6
    :param stereotype: Edge stereotype slug. Example: "calls"
    :param to_id: Target element PK. Example: 2
    :param model: Model slug for validation. Example: "yggdrasil"
    :param properties: Edge properties dict. Example: {"label": "async"}
    :return: {"changeset_id": N, "status": ..., "operation": {...}}
    :raises PermissionError: If read-only scope.
    :raises ValueError: If edge stereotype not valid for source→target types.
    """
    raise NotImplementedError()


def update_relationships_batch(
    operations: list[dict],
    model: str | None = None,
) -> dict:
    """
    Plan exactly one ChangeSet containing multiple relationship operations.

    Useful for CI agents that need to wire multiple edges in a single review unit.

    :param operations: List of operation dicts, each with from_id, stereotype,
        to_id, and optional properties. Example:
        [{"from_id": 1, "stereotype": "calls", "to_id": 2}]
    :param model: Model slug. Example: "yggdrasil"
    :return: {"changeset_id": N, "status": ..., "operation_count": N}
    :raises PermissionError: If read-only scope.
    :raises ValueError: If any operation violates edge rules.
    """
    raise NotImplementedError()


def set_model_mode(model_id: str, mode: str) -> dict:
    """
    Toggle a model between auto-approval and manual-review mode.

    :param model_id: Model slug. Example: "yggdrasil"
    :param mode: "auto" or "manual". Example: "auto"
    :return: {"model": "yggdrasil", "review_mode": "auto"}
    :raises PermissionError: If user is not a model owner/admin.
    :raises ValueError: If mode is not "auto" or "manual".
    """
    raise NotImplementedError()
