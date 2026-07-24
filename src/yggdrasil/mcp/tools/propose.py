"""
MCP propose tools for Ratatosk CLI handoff (SAO.md §18.4).

``propose_changeset`` — create a pending ChangeSet from operation dicts.
``record_ratatosk_run`` — persist RataskRun + blackboard linked to a ChangeSet.

Auth: user_id / token scope from ContextVar — never from tool args.
"""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.graph.models import Metamodel, YggdrasilModel, ensure_c4_metamodel
from yggdrasil.mcp.server import get_current_user_id, get_token_scope
from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.mcp.tools.propose")

_service = ChangeSetService()
DEFAULT_CONFIDENCE_THRESHOLD = 0.80


def ensure_model(model: str, metamodel: str = "c4") -> dict:
    """
    Resolve or create a YggdrasilModel bound to a Metamodel slug.

    :param model: Model name/slug. Example: "Yggdrasil"
    :param metamodel: Metamodel slug. Example: "c4"
    :return: {"slug": "...", "metamodel": "...", "created": bool}
    :raises PermissionError: If token is read-only.
    :raises ValueError: Unknown metamodel or binding mismatch.
    """
    _require_write_scope()
    user = _resolve_current_user()
    mm_slug = (metamodel or Metamodel.SLUG_C4).strip().lower()
    logger.info(
        "ensure_model | model=%s metamodel=%s user=%s",
        model,
        mm_slug,
        getattr(user, "pk", None),
    )
    if mm_slug == Metamodel.SLUG_C4:
        mm = ensure_c4_metamodel()
    else:
        try:
            mm = Metamodel.objects.get(slug=mm_slug)
        except Metamodel.DoesNotExist as exc:
            msg = f"Unknown metamodel slug: {mm_slug!r}. Create it in Django admin first."
            raise ValueError(msg) from exc
    slug = slugify(model)
    existing = YggdrasilModel.objects.filter(slug=slug).first()
    if existing is None:
        created = YggdrasilModel.objects.create(name=model, slug=slug, metamodel=mm)
        logger.info("ensure_model | created slug=%s metamodel=%s", created.slug, mm.slug)
        return {"slug": created.slug, "metamodel": mm.slug, "created": True}
    if existing.metamodel.slug != mm.slug:
        msg = (
            f"Model {existing.slug!r} is bound to metamodel {existing.metamodel.slug!r}; "
            f"cannot use --metamodel={mm.slug}."
        )
        raise ValueError(msg)
    return {"slug": existing.slug, "metamodel": mm.slug, "created": False}


def propose_changeset(
    model: str,
    operations: list[dict[str, Any]] | None = None,
    source: str = ChangeSet.SOURCE_RATATOSK,
    munin_reasoning: str = "",
    run_id: str = "",
    allow_empty: bool = False,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    handoff_context: dict[str, Any] | None = None,
) -> dict:
    """
    Propose a ChangeSet from structured operations (Ratatosk CLI handoff).

    High-confidence items (>= threshold) are auto-approved; below-threshold
    items remain pending for human review.

    :param model: Model slug. Example: "yggdrasil"
    :param operations: List of ``{op_type, detail, confidence}`` dicts.
    :param source: ChangeSet source. Example: "ratatosk"
    :param munin_reasoning: Summary text for the ChangeSet.
    :param run_id: Ratatosk run id. Example: "run-abc123"
    :param allow_empty: Permit zero operations (no-op audit trail).
    :param confidence_threshold: Auto-apply cutoff. Example: 0.80
    :return: changeset_id, status, applied_count, pending_count, run_url
    :raises PermissionError: If token is read-only.
    :raises ValueError: If model missing or operations invalid.
    """
    _require_write_scope()
    user = _resolve_current_user()
    ops = list(operations or [])
    logger.info(
        "propose_changeset | model=%s user=%s ops=%s source=%s run_id=%s allow_empty=%s",
        model,
        getattr(user, "pk", None),
        len(ops),
        source,
        run_id,
        allow_empty,
    )
    if handoff_context:
        synth = handoff_context.get("synthesize") or {}
        logger.info(
            "propose_changeset | handoff_context keys=%s synthesize_canonical_count=%s",
            sorted(handoff_context.keys()),
            synth.get("canonical_count"),
        )
    ymodel = _resolve_model(model)
    if not ops and not allow_empty:
        msg = "operations must not be empty"
        logger.info("propose_changeset | reject reason=empty_ops")
        raise ValueError(msg)

    from yggdrasil.munin.bootstrap_planner import (
        plan_bootstrap_changeset,
        should_enrich_ratatosk_ops,
    )

    reasoning = munin_reasoning
    enrich = should_enrich_ratatosk_ops(source, ops)
    ratatosk_op_count = len(ops)
    logger.info(
        "propose_changeset | munin_enrichment_check source=%s ratatosk_ops=%s enrich=%s",
        source,
        ratatosk_op_count,
        enrich,
    )
    if enrich:
        from yggdrasil.munin.llm_factory import build_munin_planning_llm
        from yggdrasil.munin.logging_utils import log_munin_entry, log_munin_exit

        log_munin_entry(
            "propose_changeset_munin_enrichment",
            where="mcp.tools.propose.propose_changeset",
            user_id=getattr(user, "pk", None),
            model_id=ymodel.pk,
            why="ratatosk_handoff_element_ops_only",
            ratatosk_op_count=ratatosk_op_count,
            run_id=run_id,
        )
        llm = build_munin_planning_llm()
        llm_model = getattr(llm, "model_id", type(llm).__name__)
        ops, reasoning = plan_bootstrap_changeset(
            model_id=ymodel.pk,
            element_ops=ops,
            user_id=getattr(user, "pk", None),
            llm=llm,
            confidence_threshold=confidence_threshold,
            handoff_context=handoff_context,
        )
        rel_added = len(ops) - ratatosk_op_count
        log_munin_exit(
            "propose_changeset_munin_enrichment",
            where="mcp.tools.propose.propose_changeset",
            user_id=getattr(user, "pk", None),
            success=rel_added > 0,
            llm_model=llm_model,
            relationship_ops_added=rel_added,
            summary=reasoning,
        )
    else:
        logger.info(
            "propose_changeset | munin_planner_skipped reason=%s",
            "not_ratatosk_element_only_handoff" if source == "ratatosk" else f"source={source}",
        )

    changeset = _service.propose(
        model_id=ymodel.pk,
        source=source,
        operations=ops,
        munin_reasoning=reasoning,
        run_id=run_id,
        review_mode=ChangeSet.REVIEW_MANUAL,
        user=user,
        allow_empty=allow_empty,
    )

    auto_ids = [
        item.pk for item in changeset.items.all() if float(item.confidence) >= confidence_threshold
    ]
    if auto_ids:
        changeset = _service.approve(changeset_id=changeset.pk, item_ids=auto_ids, user=user)

    applied_count = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_ACCEPTED).count()
    pending_count = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).count()
    run_url = f"https://yggdrasil.local/ratatosk-runs/{run_id}" if run_id else ""
    result = {
        "changeset_id": changeset.pk,
        "status": changeset.status,
        "applied_count": applied_count,
        "pending_count": pending_count,
        "run_url": run_url,
        "operations_count": changeset.items.count(),
        "munin_reasoning": reasoning,
    }
    logger.info(
        "propose_changeset | changeset_id=%s status=%s applied=%s pending=%s",
        changeset.pk,
        changeset.status,
        applied_count,
        pending_count,
    )
    return result


def record_ratatosk_run(
    model: str,
    run_id: str,
    repo_path: str = "",
    instructions: str = "",
    blackboard: dict[str, Any] | None = None,
    changeset_id: int | None = None,
    status: str = RataskRun.STATUS_COMPLETE,
    trigger: str = "bootstrap",
    delta_summary: dict[str, Any] | None = None,
) -> dict:
    """
    Create or update a RataskRun record with blackboard state.

    :param model: Model slug. Example: "yggdrasil"
    :param run_id: Unique run identifier. Example: "run-abc123"
    :param repo_path: Filesystem path or "(stdin)".
    :param instructions: Extra analysis instructions.
    :param blackboard: Agent blackboard JSON.
    :param changeset_id: Linked ChangeSet PK when handoff succeeded.
    :param status: running|complete|failed.
    :param trigger: bootstrap|update (stored on blackboard).
    :param delta_summary: Bucket counts dict.
    :return: {"run_id": ..., "changeset_id": ..., "status": ...}
    :raises PermissionError: If token is read-only.
    :raises ValueError: If model not found.
    """
    _require_write_scope()
    user = _resolve_current_user()
    logger.info(
        "record_ratatosk_run | model=%s run_id=%s status=%s changeset_id=%s user=%s",
        model,
        run_id,
        status,
        changeset_id,
        getattr(user, "pk", None),
    )
    ymodel = _resolve_model(model)
    board = dict(blackboard or {})
    board.setdefault("trigger", trigger)
    run, created = RataskRun.objects.get_or_create(
        run_id=run_id,
        defaults={
            "model": ymodel,
            "repo_path": repo_path or "(stdin)",
            "instructions": instructions,
            "status": status,
            "blackboard": board,
            "delta_summary": delta_summary or {},
            "triggered_by": user,
            "changeset_id": changeset_id,
        },
    )
    if not created:
        run.model = ymodel
        run.repo_path = repo_path or run.repo_path
        run.instructions = instructions or run.instructions
        run.status = status
        run.blackboard = board
        if delta_summary is not None:
            run.delta_summary = delta_summary
        if changeset_id is not None:
            run.changeset_id = changeset_id
        if status == RataskRun.STATUS_COMPLETE:
            run.completed_at = timezone.now()
        run.save()
    elif status == RataskRun.STATUS_COMPLETE:
        run.completed_at = timezone.now()
        run.save(update_fields=["completed_at"])

    result = {
        "run_id": run.run_id,
        "changeset_id": run.changeset_id,
        "status": run.status,
        "created": created,
    }
    logger.info(
        "record_ratatosk_run | run_id=%s changeset_id=%s status=%s",
        run.run_id,
        run.changeset_id,
        run.status,
    )
    return result


def _require_write_scope() -> None:
    """Reject write tools when the current token is read-only."""
    scope = get_token_scope()
    if scope == "read-only":
        msg = "permission denied: read-only token cannot write"
        logger.info("propose | reject reason=permission scope=%s", scope)
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
