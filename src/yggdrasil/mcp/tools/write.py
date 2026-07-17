"""
MCP write tools: create_element, update_element, delete_element,
create_relationship, update_relationships_batch, set_model_mode (SAO.md §18.3).

All writes go through the Munin/ChangeSet pipeline — never direct ORM.
HITL gate: delete_element and delete_relationship always queue for human review.
Auth: user_id injected server-side via ContextVar — never from tool args.
"""

from __future__ import annotations

import logging

from django.contrib.auth.models import User
from django.db.models import Q

from yggdrasil.changeset.models import ChangeSet
from yggdrasil.graph.models import YggdrasilModel
from yggdrasil.llm.base import ScriptedLLM
from yggdrasil.mcp.server import get_current_user_id
from yggdrasil.munin.agent import MuninAgent

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
    user = _resolve_current_user()
    logger.info(
        "create_element | name=%s model=%s user=%s",
        name,
        model,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model)
    llm = ScriptedLLM(responses=[f"Proposed Add Element for {name}"])
    agent = MuninAgent(
        llm=llm,
        model_id=ymodel.pk,
        user_id=getattr(user, "pk", None),
    )
    message = (
        f"TOOL:create_element|name={name}|stereotype={stereotype}"
        f"|package={package or ''}|owner={owner}|model={ymodel.slug}"
    )
    if properties:
        message += f"|properties={properties!r}"
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        msg = "Munin did not produce a ChangeSet for create_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    op = cs.items.first()
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operation": {
            "op_type": op.op_type if op else "add_element",
            "detail": op.detail if op else {},
        },
    }
    logger.info(
        "create_element | name=%s changeset_id=%s status=%s",
        name,
        cs.pk,
        cs.status,
    )
    return result


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
    to_id: int,
    stereotype: str,
    model: str | None = None,
    properties: dict | None = None,
) -> dict:
    """
    Propose a new relationship between two elements.

    :param from_id: Source element PK. Example: 6
    :param to_id: Target element PK. Example: 2
    :param stereotype: Edge stereotype slug. Example: "calls"
    :param model: Model slug. Example: "yggdrasil"
    :param properties: Edge properties. Example: {"label": "HTTP"}
    :return: {"changeset_id": N, "status": ..., "operation": {...}}
    """
    raise NotImplementedError()


def update_relationships_batch(
    operations: list[dict],
    model: str | None = None,
) -> dict:
    """
    Propose a batch of relationship create/update/delete operations.

    :param operations: List of op dicts. Example:
        [{"op": "create", "from_id": 1, "to_id": 2, "stereotype": "calls"}]
    :param model: Model slug. Example: "yggdrasil"
    :return: {"changeset_id": N, "status": "pending", "operations_count": N}
    """
    raise NotImplementedError()


def set_model_mode(model_id: str, mode: str) -> dict:
    """
    Toggle a model between auto-approval and manual-review mode.

    :param model_id: Model slug. Example: "yggdrasil"
    :param mode: "auto" or "manual". Example: "auto"
    :return: {"model": "yggdrasil", "review_mode": "auto"}
    """
    raise NotImplementedError()


def _resolve_current_user() -> User | None:
    """Load authenticated user from MCP ContextVar."""
    user_id = get_current_user_id()
    if user_id is None:
        return None
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        msg = f"MCP user_id={user_id} not found"
        raise PermissionError(msg) from exc


def _resolve_model(model: str) -> YggdrasilModel:
    """Resolve model by slug or name."""
    try:
        return YggdrasilModel.objects.get(Q(slug__iexact=model) | Q(name__iexact=model))
    except YggdrasilModel.DoesNotExist as exc:
        msg = f"Model {model!r} not found"
        raise ValueError(msg) from exc
