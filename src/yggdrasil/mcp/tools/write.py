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
from yggdrasil.graph.models import Element, YggdrasilModel
from yggdrasil.mcp.server import get_current_user_id, get_token_scope
from yggdrasil.munin.agent import MuninAgent, set_model_review_mode
from yggdrasil.munin.llm_factory import build_munin_planning_llm

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
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "create_element | name=%s model=%s user=%s",
        name,
        model,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model)
    llm = build_munin_planning_llm()
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
    fields: dict | None = None,
) -> dict:
    """
    Propose updating specific fields of an existing element.

    Only provided fields are changed. Produces an Update Element operation
    with a before/after diff in the ChangeSet detail.

    :param id: Element PK. Example: 3
    :param model: Model slug for validation. Example: "yggdrasil"
    :param fields: Fields to update (name, owner, package, properties).
        Example: ``{"owner": "fulfillment-team"}``
    :return: {"changeset_id": N, "status": ..., "operation": {...}}
    :raises PermissionError: If current user token has read-only scope.
    :raises ValueError: If element not found or fields empty.
    """
    _require_write_scope()
    user = _resolve_current_user()
    updates = fields or {}
    logger.info(
        "update_element | id=%s model=%s fields=%s user=%s",
        id,
        model,
        sorted(updates.keys()),
        getattr(user, "pk", None),
    )
    if not updates:
        msg = "update_element requires at least one field to update"
        raise ValueError(msg)
    ymodel = _resolve_model(model) if model else None
    model_id = ymodel.pk if ymodel else _model_id_for_element(id)
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    field_parts = "|".join(f"{key}={value}" for key, value in updates.items())
    message = f"TOOL:update_element|id={id}|{field_parts}"
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        msg = "Munin did not produce a ChangeSet for update_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    op = cs.items.first()
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operation": {
            "op_type": op.op_type if op else "update_element",
            "detail": op.detail if op else {},
        },
    }
    logger.info(
        "update_element | id=%s changeset_id=%s status=%s",
        id,
        cs.pk,
        cs.status,
    )
    return result


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
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "delete_element | id=%s model=%s user=%s",
        id,
        model,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model) if model else None
    model_id = ymodel.pk if ymodel else _model_id_for_element(id)
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    resp = agent.chat(f"TOOL:delete_element|id={id}", history=[])
    if resp.changeset_id is None:
        msg = "Munin did not produce a ChangeSet for delete_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    blast_radius = next(
        (
            call.get("blast_radius")
            for call in resp.tool_calls
            if call.get("tool") == "delete_element"
        ),
        0,
    )
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "blast_radius": blast_radius,
        "operation": {
            "op_type": "delete_element",
            "detail": cs.items.first().detail if cs.items.exists() else {},
        },
    }
    logger.info(
        "delete_element | id=%s changeset_id=%s blast_radius=%s",
        id,
        cs.pk,
        blast_radius,
    )
    return result


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
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "create_relationship | from=%s to=%s stereotype=%s user=%s",
        from_id,
        to_id,
        stereotype,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model) if model else None
    model_id = ymodel.pk if ymodel else _model_id_for_element(from_id)
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    props = f"|properties={properties!r}" if properties else ""
    message = (
        f"TOOL:create_relationship|from_id={from_id}|to_id={to_id}"
        f"|stereotype={stereotype}{props}"
    )
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        msg = "Munin did not produce a ChangeSet for create_relationship"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    op = cs.items.first()
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operation": {
            "op_type": op.op_type if op else "add_relationship",
            "detail": op.detail if op else {},
        },
        "edge_rule_validated": next(
            (
                call.get("edge_rule_validated")
                for call in resp.tool_calls
                if call.get("tool") == "create_relationship"
            ),
            True,
        ),
    }
    logger.info(
        "create_relationship | from=%s to=%s changeset_id=%s",
        from_id,
        to_id,
        cs.pk,
    )
    return result


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
    _require_write_scope()
    user = _resolve_current_user()
    if not operations:
        msg = "update_relationships_batch requires at least one operation"
        raise ValueError(msg)
    logger.info(
        "update_relationships_batch | ops=%s model=%s user=%s",
        len(operations),
        model,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model) if model else None
    first_from = operations[0].get("from_id") or operations[0].get("source_id")
    model_id = ymodel.pk if ymodel else _model_id_for_element(int(first_from))
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    message = f"TOOL:update_relationships_batch|count={len(operations)}|operations={operations!r}"
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        msg = "Munin did not produce a ChangeSet for update_relationships_batch"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operations_count": cs.items.count(),
    }
    logger.info(
        "update_relationships_batch | changeset_id=%s ops=%s",
        cs.pk,
        result["operations_count"],
    )
    return result


def set_model_mode(model_id: str, mode: str) -> dict:
    """
    Toggle a model between auto-approval and manual-review mode.

    :param model_id: Model slug. Example: "yggdrasil"
    :param mode: "auto" or "manual". Example: "auto"
    :return: {"model": "yggdrasil", "review_mode": "auto"}
    """
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "set_model_mode | model_id=%s mode=%s user=%s",
        model_id,
        mode,
        getattr(user, "pk", None),
    )
    normalized = mode.strip().lower()
    if normalized not in {"auto", "manual"}:
        msg = f"Invalid mode={mode!r}; expected 'auto' or 'manual'"
        raise ValueError(msg)
    ymodel = _resolve_model(model_id)
    set_model_review_mode(ymodel.pk, normalized)
    result = {"model": ymodel.slug, "review_mode": normalized}
    logger.info("set_model_mode | model=%s review_mode=%s", ymodel.slug, normalized)
    return result


def _require_write_scope() -> None:
    """Reject write tools when the current token is read-only."""
    scope = get_token_scope()
    if scope == "read-only":
        msg = "permission denied: read-only token cannot write"
        logger.info("_require_write_scope | denied scope=%s", scope)
        raise PermissionError(msg)


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


def _model_id_for_element(element_id: int) -> int:
    """Return the owning model PK for an element."""
    try:
        return Element.objects.values_list("model_id", flat=True).get(pk=element_id)
    except Element.DoesNotExist as exc:
        msg = f"Element id={element_id} not found"
        raise ValueError(msg) from exc
