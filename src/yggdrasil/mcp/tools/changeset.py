"""
MCP ChangeSet tools: approve_changeset, reject_changeset, do_other_changeset
(SAO.md §18.3 — tool inventory, ChangeSet review tools).

These are the headless equivalents of the GUI ChangeSet review screen.
Auth: user_id injected server-side — never from tool args.
"""

from __future__ import annotations

import logging

from django.contrib.auth.models import User

from yggdrasil.changeset.models import ChangeSetItem, MuninRule
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.mcp.server import get_current_user_id, get_token_scope

logger = logging.getLogger("yggdrasil.mcp.tools.changeset")

_service = ChangeSetService()


def approve_changeset(
    id: int,
    item_ids: list[int] | None = None,
) -> dict:
    """
    Apply all (or specified) pending operations in a ChangeSet.

    :param id: ChangeSet PK. Example: 1
    :param item_ids: Specific ChangeSetItem PKs to apply.
        None = apply all pending. Example: [1, 2]
    :return: {"changeset_id": N, "applied_count": N, "status": "applied"|"pending"}
    :raises PermissionError: If current user lacks write access.
    :raises ValueError: If ChangeSet not found or already applied.
    """
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "approve_changeset | id=%s user=%s item_ids=%s",
        id,
        getattr(user, "pk", None),
        item_ids,
    )
    changeset = _service.approve(changeset_id=id, item_ids=item_ids, user=user)
    applied_count = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_ACCEPTED).count()
    if item_ids is not None:
        applied_count = changeset.items.filter(
            pk__in=item_ids,
            status=ChangeSetItem.ITEM_STATUS_ACCEPTED,
        ).count()
    result = {
        "changeset_id": changeset.pk,
        "applied_count": applied_count,
        "status": changeset.status,
    }
    logger.info(
        "approve_changeset | id=%s user=%s result=%s",
        id,
        getattr(user, "pk", None),
        result,
    )
    return result


def _resolve_current_user() -> User | None:
    """Load the authenticated user from MCP ContextVar (never from tool args)."""
    user_id = get_current_user_id()
    if user_id is None:
        logger.info("approve_changeset | no user in ContextVar — proceeding as system")
        return None
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        msg = f"MCP user_id={user_id} not found"
        raise PermissionError(msg) from exc


def _require_write_scope() -> None:
    """Reject write tools when the current token is read-only."""
    scope = get_token_scope()
    if scope == "read-only":
        msg = "permission denied: read-only token cannot write"
        logger.info("changeset | reject reason=permission scope=%s", scope)
        raise PermissionError(msg)


def reject_changeset(
    id: int,
    item_ids: list[int] | None = None,
    reason: str = "",
) -> dict:
    """
    Reject all (or specified) pending operations; optionally learn from reason.

    When reason is provided, a MuninRule is created so Munin avoids this
    pattern in future runs (SAO.md §17.5 — Learning module).

    :param id: ChangeSet PK. Example: 1
    :param item_ids: Specific ChangeSetItem PKs to reject. None = reject all.
    :param reason: Rejection reason. Example:
        "Code diagram is for repository structure, not runtime services"
    :return: {"changeset_id": N, "rejected_count": N, "rule_created": bool}
    :raises PermissionError: If current user lacks write access.
    :raises ValueError: If ChangeSet not found.
    """
    user = _resolve_current_user()
    logger.info(
        "reject_changeset | id=%s user=%s item_ids=%s reason=%r",
        id,
        getattr(user, "pk", None),
        item_ids,
        reason[:80] if reason else "",
    )
    before_rules = MuninRule.objects.filter(source_item__changeset_id=id).count() if reason else 0
    changeset = _service.reject(
        changeset_id=id,
        item_ids=item_ids,
        reason=reason,
        user=user,
        learn=bool(reason),
    )
    rejected_qs = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_REJECTED)
    if item_ids is not None:
        rejected_qs = rejected_qs.filter(pk__in=item_ids)
    rejected_count = rejected_qs.count()
    rule_created = False
    if reason:
        after_rules = MuninRule.objects.filter(source_item__changeset_id=id).count()
        rule_created = after_rules > before_rules
    result = {
        "changeset_id": changeset.pk,
        "rejected_count": rejected_count,
        "rule_created": rule_created,
    }
    logger.info(
        "reject_changeset | id=%s user=%s result=%s",
        id,
        getattr(user, "pk", None),
        result,
    )
    return result


def do_other_changeset(
    id: int,
    item_ids: list[int],
    instructions: str,
) -> dict:
    """
    Reject specified items and queue Munin to re-plan them with instructions.

    Instructions are appended to LEARNED (MuninRule) for future reference.
    Munin re-processes asynchronously; the response returns the original
    ChangeSet ID and the queued re-plan task ID.

    :param id: ChangeSet PK. Example: 1
    :param item_ids: ChangeSetItem PKs to re-plan. Example: [3]
    :param instructions: Guidance for Munin's re-plan. Example:
        "don't add this to the Container diagram, it's an external system"
    :return: {"changeset_id": N, "redirected_count": N, "replan_task_id": "..."}
    :raises PermissionError: If read-only scope.
    :raises ValueError: If item_ids is empty or ChangeSet not found.
    """
    user = _resolve_current_user()
    logger.info(
        "do_other_changeset | id=%s user=%s item_ids=%s instructions=%r",
        id,
        getattr(user, "pk", None),
        item_ids,
        instructions[:80] if instructions else "",
    )
    if not item_ids:
        msg = "do_other_changeset requires at least one item_id"
        raise ValueError(msg)
    changeset = _service.do_other(
        changeset_id=id,
        item_ids=item_ids,
        instructions=instructions,
        user=user,
    )
    replacements = getattr(changeset, "_do_other_replacements", [])
    result = {
        "changeset_id": changeset.pk,
        "redirected_count": len(item_ids),
        "replan_task_id": f"replan-{id}-{'-'.join(str(i) for i in item_ids)}",
        "replacement_changeset_ids": replacements,
    }
    logger.info(
        "do_other_changeset | id=%s user=%s result=%s",
        id,
        getattr(user, "pk", None),
        result,
    )
    return result


def ask_munin(question: str, model: str | None = None) -> dict:
    """
    Ask Munin a natural-language question about the architecture graph.

    Munin has access to the full graph via query tools. Returns a structured
    response with cited element references and optional navigation hints.

    :param question: Natural language query. Example:
        "What domain objects have changed since Jan?"
    :param model: Model slug to scope the question. Example: "yggdrasil"
    :return: {"answer": "...", "cited_elements": [...], "navigation_url": "..."|None}
    :raises PermissionError: If current user has no read access.
    """
    from django.db.models import Q

    from yggdrasil.graph.models import YggdrasilModel
    from yggdrasil.munin.agent import MuninAgent
    from yggdrasil.munin.llm_factory import build_munin_planning_llm

    user = _resolve_current_user()
    logger.info(
        "ask_munin | user=%s model=%s question=%r",
        getattr(user, "pk", None),
        model,
        question[:80],
    )
    ymodel = None
    if model:
        ymodel = YggdrasilModel.objects.filter(
            Q(slug__iexact=model) | Q(name__iexact=model)
        ).first()
    if ymodel is None:
        ymodel = YggdrasilModel.objects.filter(slug="yggdrasil").first()
    if ymodel is None:
        msg = "No Yggdrasil model available for ask_munin"
        raise ValueError(msg)
    agent = MuninAgent(
        llm=build_munin_planning_llm(),
        model_id=ymodel.pk,
        user_id=getattr(user, "pk", None),
    )
    resp = agent.chat(question, history=[])
    result = {
        "answer": resp.text,
        "cited_elements": resp.cited_elements,
        "navigation_url": resp.navigation_url,
    }
    logger.info("ask_munin | cites=%s", len(resp.cited_elements))
    return result
