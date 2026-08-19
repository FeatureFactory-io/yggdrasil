"""
MCP write tools: create_element, update_element, delete_element,
create_relationship, update_relationships_batch, set_model_mode (SAO.md §18.3).

All writes go through the Munin/ChangeSet pipeline — never direct ORM.
HITL gate: delete_element and delete_relationship always queue for human review.
Auth: user_id injected server-side via ContextVar — never from tool args.
"""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.models import User

from yggdrasil.changeset.models import ChangeSet
from yggdrasil.graph import browse_service
from yggdrasil.graph.models import Element, YggdrasilModel
from yggdrasil.mcp.server import get_current_user_id, get_token_scope
from yggdrasil.munin.agent import MuninAgent, set_model_review_mode
from yggdrasil.munin.llm_factory import build_munin_planning_llm

logger = logging.getLogger("yggdrasil.mcp.tools.write")


def _log(where: str, beat: str, **fields: object) -> None:
    """Emit a grep-friendly MCP write-tool story beat."""
    extras = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("%s | %s | %s", where, beat, extras)


def create_element(
    name: str,
    stereotype: str,
    model: str,
    package: str | None = None,
    owner: str = "",
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Propose adding a new element via the Munin/ChangeSet pipeline.

    In auto-approval mode the element is applied immediately.
    In manual-review mode a pending ChangeSet is returned.

    :param name: Element name. Example: "Notification Service"
    :param stereotype: Stereotype slug. Example: "container"
    :param model: Model slug. Example: "yggdrasil"
    :param package: Package slug. Example: "technology"
    :param owner: Owner team. Example: "payments-team"
    :param properties: Stereotype-driven attributes dict[str, Any]. Example: {"framework": "FastAPI"}
    :return: {"changeset_id": N, "status": "applied"|"pending", "operation": {...}}
    :raises PermissionError: If current user token has read-only scope.
    :raises ValueError: If stereotype or model not found.
    """
    _log(
        "create_element",
        "entry",
        name=name,
        model=model,
        stereotype=stereotype,
        package=package,
        user=get_current_user_id(),
    )
    _require_write_scope()
    user = _resolve_current_user()
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
        _log("create_element", "error", reason="no_changeset", name=name)
        msg = "Munin did not produce a ChangeSet for create_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    _log(
        "create_element",
        "processing",
        changeset_id=cs.pk,
        status=cs.status,
        munin_ok=True,
    )
    op = cs.items.first()
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operation": {
            "op_type": op.op_type if op else "add_element",
            "detail": op.detail if op else {},
        },
    }
    _log(
        "create_element",
        "exit",
        name=name,
        changeset_id=cs.pk,
        status=cs.status,
    )
    return result


def update_element(
    id: int,
    model: str | None = None,
    fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
    updates = fields or {}
    _log(
        "update_element",
        "entry",
        id=id,
        model=model,
        fields=sorted(updates.keys()),
        user=get_current_user_id(),
    )
    _require_write_scope()
    user = _resolve_current_user()
    if not updates:
        _log("update_element", "validation", reason="empty_fields", id=id)
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
        _log("update_element", "error", reason="no_changeset", id=id)
        msg = "Munin did not produce a ChangeSet for update_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    _log(
        "update_element",
        "processing",
        changeset_id=cs.pk,
        status=cs.status,
        munin_ok=True,
    )
    op = cs.items.first()
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operation": {
            "op_type": op.op_type if op else "update_element",
            "detail": op.detail if op else {},
        },
    }
    _log("update_element", "exit", id=id, changeset_id=cs.pk, status=cs.status)
    return result


def delete_element(id: int, model: str | None = None) -> dict[str, Any]:
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
    _log("delete_element", "entry", id=id, model=model, user=get_current_user_id())
    _require_write_scope()
    user = _resolve_current_user()
    ymodel = _resolve_model(model) if model else None
    model_id = ymodel.pk if ymodel else _model_id_for_element(id)
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    resp = agent.chat(f"TOOL:delete_element|id={id}", history=[])
    if resp.changeset_id is None:
        _log("delete_element", "error", reason="no_changeset", id=id)
        msg = "Munin did not produce a ChangeSet for delete_element"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    _log(
        "delete_element",
        "processing",
        changeset_id=cs.pk,
        status=cs.status,
        munin_ok=True,
    )
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
            "detail": (first.detail if (first := cs.items.first()) else {}),
        },
    }
    _log(
        "delete_element",
        "exit",
        id=id,
        changeset_id=cs.pk,
        blast_radius=blast_radius,
    )
    return result


def create_relationship(
    from_id: int,
    to_id: int,
    stereotype: str,
    model: str | None = None,
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Propose a new relationship between two elements.

    :param from_id: Source element PK. Example: 6
    :param to_id: Target element PK. Example: 2
    :param stereotype: Edge stereotype slug. Example: "calls"
    :param model: Model slug. Example: "yggdrasil"
    :param properties: Edge properties. Example: {"label": "HTTP"}
    :return: {"changeset_id": N, "status": ..., "operation": {...}}
    """
    _log(
        "create_relationship",
        "entry",
        **{
            "from": from_id,
            "to": to_id,
            "stereotype": stereotype,
            "model": model,
            "user": get_current_user_id(),
        },
    )
    _require_write_scope()
    user = _resolve_current_user()
    ymodel = _resolve_model(model) if model else None
    model_id = ymodel.pk if ymodel else _model_id_for_element(from_id)
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    props = f"|properties={properties!r}" if properties else ""
    message = (
        f"TOOL:create_relationship|from_id={from_id}|to_id={to_id}|stereotype={stereotype}{props}"
    )
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        _log("create_relationship", "error", reason="no_changeset", from_id=from_id, to_id=to_id)
        msg = "Munin did not produce a ChangeSet for create_relationship"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    _log(
        "create_relationship",
        "processing",
        changeset_id=cs.pk,
        status=cs.status,
        munin_ok=True,
    )
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
    _log(
        "create_relationship",
        "exit",
        **{"from": from_id, "to": to_id, "changeset_id": cs.pk},
    )
    return result


def update_relationships_batch(
    operations: list[dict[str, Any]],
    model: str | None = None,
) -> dict[str, Any]:
    """
    Propose a batch of relationship create/update/delete operations.

    :param operations: List of op dicts. Example:
        [{"op": "create", "from_id": 1, "to_id": 2, "stereotype": "calls"}]
    :param model: Model slug. Example: "yggdrasil"
    :return: {"changeset_id": N, "status": "pending", "operations_count": N}
    """
    _log(
        "update_relationships_batch",
        "entry",
        ops=len(operations),
        model=model,
        user=get_current_user_id(),
    )
    _require_write_scope()
    user = _resolve_current_user()
    if not operations:
        _log("update_relationships_batch", "validation", reason="empty_operations")
        msg = "update_relationships_batch requires at least one operation"
        raise ValueError(msg)
    ymodel = _resolve_model(model) if model else None
    first_from = operations[0].get("from_id") or operations[0].get("source_id")
    model_id = ymodel.pk if ymodel else _model_id_for_element(int(first_from or 0))
    llm = build_munin_planning_llm()
    agent = MuninAgent(llm=llm, model_id=model_id, user_id=getattr(user, "pk", None))
    message = f"TOOL:update_relationships_batch|count={len(operations)}|operations={operations!r}"
    resp = agent.chat(message, history=[])
    if resp.changeset_id is None:
        _log("update_relationships_batch", "error", reason="no_changeset")
        msg = "Munin did not produce a ChangeSet for update_relationships_batch"
        raise ValueError(msg)
    cs = ChangeSet.objects.get(pk=resp.changeset_id)
    _log(
        "update_relationships_batch",
        "processing",
        changeset_id=cs.pk,
        status=cs.status,
        munin_ok=True,
    )
    result = {
        "changeset_id": cs.pk,
        "status": cs.status,
        "operations_count": cs.items.count(),
    }
    _log(
        "update_relationships_batch",
        "exit",
        changeset_id=cs.pk,
        ops=result["operations_count"],
    )
    return result


def set_model_mode(model_id: str, mode: str) -> dict[str, Any]:
    """
    Toggle a model between auto-approval and manual-review mode.

    :param model_id: Model slug. Example: "yggdrasil"
    :param mode: "auto" or "manual". Example: "auto"
    :return: {"model": "yggdrasil", "review_mode": "auto"}
    """
    _log(
        "set_model_mode",
        "entry",
        model_id=model_id,
        mode=mode,
        user=get_current_user_id(),
    )
    _require_write_scope()
    user = _resolve_current_user()
    normalized = mode.strip().lower()
    if normalized not in {"auto", "manual"}:
        _log("set_model_mode", "validation", reason="invalid_mode", mode=mode)
        msg = f"Invalid mode={mode!r}; expected 'auto' or 'manual'"
        raise ValueError(msg)
    ymodel = _resolve_model(model_id)
    set_model_review_mode(ymodel.pk, normalized)
    result = {"model": ymodel.slug, "review_mode": normalized}
    _log(
        "set_model_mode",
        "exit",
        model=ymodel.slug,
        review_mode=normalized,
        user=getattr(user, "pk", None),
    )
    return result


def _require_write_scope() -> None:
    """Reject write tools when the current token is read-only."""
    scope = get_token_scope()
    if scope == "read-only":
        msg = "permission denied: read-only token cannot write"
        _log("_require_write_scope", "branch", reason="read_only", scope=scope)
        raise PermissionError(msg)
    _log("_require_write_scope", "branch", reason="ok", scope=scope)


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
    return browse_service.resolve_model(model)


def _model_id_for_element(element_id: int) -> int:
    """Return the owning model PK for an element."""
    try:
        return Element.objects.values_list("model_id", flat=True).get(pk=element_id)
    except Element.DoesNotExist as exc:
        msg = f"Element id={element_id} not found"
        raise ValueError(msg) from exc
