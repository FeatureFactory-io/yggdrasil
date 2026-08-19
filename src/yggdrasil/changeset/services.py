"""
ChangeSet service layer: all write operations go through here.

Views, MCP tools, and Munin never touch ORM directly — they call
ChangeSetService methods (SAO.md §3 — layer separation).

All operations are transactional (SAO.md §7 — ChangeSet atomicity).

Dependency rules: changeset.services → graph ORM, changeset ORM only.
Never import from munin, ratatosk, or mcp here.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem, MuninRule
from yggdrasil.graph.models import (
    Diagram,
    Element,
    Package,
    Relationship,
    Stereotype,
    YggdrasilModel,
)

if TYPE_CHECKING:
    import builtins

    from django.contrib.auth.models import User
    from django.db.models import QuerySet

logger = logging.getLogger("yggdrasil.changeset")


def _story(where: str, beat: str, *, level: int = logging.INFO, **fields: object) -> None:
    """Emit a grep-friendly log story line: ``Class.method | beat | key=value``."""
    payload = " ".join(f"{key}={value}" for key, value in fields.items())
    if payload:
        logger.log(level, "%s | %s | %s", where, beat, payload)
        return
    logger.log(level, "%s | %s", where, beat)


def _op_type_counts(ops: list[Any]) -> dict[str, int]:
    """Count op_type values from dicts, ChangeSetItem rows, or type strings."""
    types: list[str] = []
    for op in ops:
        if isinstance(op, dict):
            types.append(str(op.get("op_type", "unknown")))
        elif isinstance(op, str):
            types.append(op)
        else:
            types.append(str(op.op_type))
    return dict(Counter(types))


_INVERSE_OP_TYPES: dict[str, str] = {
    ChangeSetItem.OP_ADD_ELEMENT: ChangeSetItem.OP_DELETE_ELEMENT,
    ChangeSetItem.OP_DELETE_ELEMENT: ChangeSetItem.OP_ADD_ELEMENT,
    ChangeSetItem.OP_ADD_RELATIONSHIP: ChangeSetItem.OP_DELETE_RELATIONSHIP,
    ChangeSetItem.OP_DELETE_RELATIONSHIP: ChangeSetItem.OP_ADD_RELATIONSHIP,
    ChangeSetItem.OP_UPDATE_ELEMENT: ChangeSetItem.OP_UPDATE_ELEMENT,
    ChangeSetItem.OP_ADD_TO_DIAGRAM: ChangeSetItem.OP_ADD_TO_DIAGRAM,
}


class ChangeSetService:
    """
    Create, query, approve, reject, and rollback ChangeSets.

    All mutating methods run inside a DB transaction. Callers receive the
    updated ChangeSet instance; they must not re-use stale references.

    :Example:

    >>> svc = ChangeSetService()
    >>> cs = svc.propose(model_id=1, source="mcp", operations=[...], user=request.user)
    >>> cs = svc.approve(changeset_id=cs.pk, user=request.user)
    """

    def propose(
        self,
        model_id: int,
        source: str,
        operations: builtins.list[dict[str, Any]],
        munin_reasoning: str = "",
        run_id: str = "",
        review_mode: str = ChangeSet.REVIEW_MANUAL,
        user: User | None = None,
        allow_empty: bool = False,
    ) -> ChangeSet:
        """
        Create a new pending ChangeSet with the given operations.

        :param model_id: YggdrasilModel PK. Example: 1
        :param source: One of "ratatosk", "human", "mcp". Example: "mcp"
        :param operations: List of operation dicts, each with keys
            ``op_type``, ``detail``, ``confidence``. Example:
            [{"op_type": "add_element", "detail": {...}, "confidence": 0.92}]
        :param munin_reasoning: Munin's natural-language explanation.
        :param run_id: Ratatosk run identifier if source=ratatosk. Example: "run-003"
        :param review_mode: "auto" or "manual". Example: "manual"
        :param user: Requesting user (for audit). May be None for CI/system.
        :param allow_empty: When True, permit zero operations (Ratatosk no-op runs).
        :return: Created ChangeSet with status="pending".
        :raises ValueError: If operations is empty (unless allow_empty) or source is invalid.

        :Example:

        >>> cs = svc.propose(model_id=1, source="mcp",
        ...     operations=[{"op_type": "add_element", "detail": {...}, "confidence": 0.9}])
        >>> cs.status
        'pending'
        """
        user_id = getattr(user, "pk", None)
        _story(
            "ChangeSetService.propose",
            "entry",
            model_id=model_id,
            source=source,
            ops=len(operations),
            user_id=user_id,
            allow_empty=allow_empty,
        )
        self._validate_propose(operations, source, allow_empty)
        with transaction.atomic():
            model = self._get_model_or_raise(model_id)
            changeset = self._create_pending_changeset(
                model, source, review_mode, run_id, munin_reasoning
            )
            self._create_operation_items(changeset, operations)
        counts = _op_type_counts(operations)
        _story(
            "ChangeSetService.propose",
            "processing",
            item_count=len(operations),
            **counts,
        )
        _story(
            "ChangeSetService.propose",
            "exit",
            changeset_id=changeset.pk,
            status=changeset.status,
            item_count=len(operations),
        )
        return changeset

    def approve(
        self,
        changeset_id: int,
        item_ids: builtins.list[int] | None = None,
        user: User | None = None,
    ) -> ChangeSet:
        """
        Apply all (or specified) pending operations in a ChangeSet to the graph.

        Runs inside a single DB transaction — all-or-nothing per call.
        If ``item_ids`` is provided, only those items are applied;
        others remain pending for a subsequent call.

        :param changeset_id: ChangeSet PK. Example: 1
        :param item_ids: Optional list[Any] of ChangeSetItem PKs to apply.
            None = apply all pending items. Example: [1, 2]
        :param user: Actor applying the changeset.
        :return: Updated ChangeSet (status="applied" if all items resolved).
        :raises ValueError: If changeset_id not found or already applied.
        :raises PermissionError: If user lacks write permission.
        :raises IntegrityError: If a graph operation violates DB constraints.

        :Example:

        >>> cs = svc.approve(changeset_id=1)
        >>> cs.status
        'applied'
        """
        user_id = getattr(user, "pk", None)
        _story(
            "ChangeSetService.approve",
            "entry",
            changeset_id=changeset_id,
            item_ids=item_ids,
            user=user_id,
        )
        with transaction.atomic():
            changeset = self._get_pending_changeset(changeset_id)
            targets = self._select_pending_items(changeset, item_ids)
            _story(
                "ChangeSetService.approve",
                "processing",
                selected_count=len(targets),
            )
            for item in targets:
                self._apply_item(item)
                item.status = ChangeSetItem.ITEM_STATUS_ACCEPTED
                item.save(update_fields=["status", "detail"])
            self._finalize_changeset_status(changeset, user)
        _story(
            "ChangeSetService.approve",
            "exit",
            changeset_id=changeset.pk,
            status=changeset.status,
            applied_count=len(targets),
        )
        return changeset

    def reject(
        self,
        changeset_id: int,
        item_ids: builtins.list[int] | None = None,
        reason: str = "",
        user: User | None = None,
        learn: bool = True,
    ) -> ChangeSet:
        """
        Reject all (or specified) pending operations; optionally learn from the reason.

        If ``reason`` is provided and ``learn=True``, a MuninRule is created
        so Munin avoids the same operation in future runs.

        :param changeset_id: ChangeSet PK. Example: 1
        :param item_ids: Optional list[Any] of ChangeSetItem PKs to reject.
            None = reject all pending. Example: [3]
        :param reason: Human-readable reason for rejection. Example:
            "Code diagram is for repository structure, not runtime services"
        :param user: Actor performing the rejection.
        :param learn: If True and reason is provided, create a MuninRule.
        :return: Updated ChangeSet.
        :raises ValueError: If changeset_id not found.

        :Example:

        >>> cs = svc.reject(changeset_id=1, item_ids=[3], reason="Not applicable")
        >>> MuninRule.objects.filter(source_item__changeset_id=1).count()
        1
        """
        user_id = getattr(user, "pk", None)
        _story(
            "ChangeSetService.reject",
            "entry",
            changeset_id=changeset_id,
            item_ids=item_ids,
            learn=learn,
            user=user_id,
        )
        self._log_reject_learn_branch(learn, reason)
        with transaction.atomic():
            changeset = self._get_pending_changeset(changeset_id)
            targets = self._select_pending_items(changeset, item_ids)
            for item in targets:
                item.status = ChangeSetItem.ITEM_STATUS_REJECTED
                item.rejection_reason = reason
                item.save(update_fields=["status", "rejection_reason"])
                if learn and reason:
                    self._create_munin_rule(item, reason, user)
            self._finalize_changeset_status(changeset, user)
        _story(
            "ChangeSetService.reject",
            "exit",
            rejected_count=len(targets),
            status=changeset.status,
        )
        return changeset

    def do_other(
        self,
        changeset_id: int,
        item_ids: builtins.list[int],
        instructions: str,
        user: User | None = None,
    ) -> ChangeSet:
        """
        Reject specified items and queue Munin to re-plan them with instructions.

        The instructions are appended to LEARNED (MuninRule) so they influence
        future runs. The re-planned items arrive as a new ChangeSet.

        :param changeset_id: ChangeSet PK. Example: 1
        :param item_ids: ChangeSetItem PKs to re-plan. Example: [3]
        :param instructions: Munin guidance for the re-plan. Example:
            "don't add this to the Container diagram, it's an external system"
        :param user: Actor performing the redirection.
        :return: The original ChangeSet (with items rejected).
            The new ChangeSet is created asynchronously by Munin.
        :raises ValueError: If item_ids is empty.

        :Example:

        >>> cs = svc.do_other(changeset_id=1, item_ids=[3],
        ...     instructions="It's an external system")
        """
        user_id = getattr(user, "pk", None)
        _story(
            "ChangeSetService.do_other",
            "entry",
            changeset_id=changeset_id,
            item_ids=item_ids,
            user=user_id,
        )
        self._validate_do_other(item_ids, instructions)
        # Reject + LEARNED first; Munin re-plan is synchronous for AT/MCP.
        changeset = self.reject(
            changeset_id=changeset_id,
            item_ids=item_ids,
            reason=instructions,
            user=user,
            learn=True,
        )
        replacement_ids = self._replan_rejected_items(changeset, item_ids, instructions, user)
        # Stash for MCP tool response without changing the return contract.
        changeset._do_other_replacements = replacement_ids  # type: ignore[attr-defined]
        _story(
            "ChangeSetService.do_other",
            "processing",
            replacement_ids=replacement_ids,
        )
        _story(
            "ChangeSetService.do_other",
            "exit",
            changeset_id=changeset.pk,
            redirected=len(item_ids),
            replacements=replacement_ids,
        )
        return changeset

    def rollback(
        self,
        changeset_id: int,
        user: User | None = None,
    ) -> ChangeSet:
        """
        Create a new ChangeSet that reverses all applied operations in changeset_id.

        The rollback ChangeSet has source="rollback" and contains inverse
        operations (add_element → delete_element, and so on).

        :param changeset_id: Applied ChangeSet to roll back. Example: 2
        :param user: Actor performing the rollback.
        :return: New rollback ChangeSet with status="pending".
        :raises ValueError: If changeset_id not found or not applied.

        :Example:

        >>> rollback_cs = svc.rollback(changeset_id=2)
        >>> rollback_cs.source
        'rollback'
        """
        user_id = getattr(user, "pk", None)
        _story(
            "ChangeSetService.rollback",
            "entry",
            changeset_id=changeset_id,
            user=user_id,
        )
        with transaction.atomic():
            source_cs = self._get_applied_changeset(changeset_id)
            accepted = self._accepted_items(source_cs)
            inverse_types = [
                _INVERSE_OP_TYPES[item.op_type]
                for item in accepted
                if item.op_type in _INVERSE_OP_TYPES
            ]
            _story(
                "ChangeSetService.rollback",
                "processing",
                reversing=len(accepted),
                **_op_type_counts(inverse_types),
            )
            rollback_cs = self._create_rollback_changeset(source_cs, accepted)
        _story(
            "ChangeSetService.rollback",
            "exit",
            rollback_id=rollback_cs.pk,
            reversing=len(accepted),
        )
        return rollback_cs

    def get(self, changeset_id: int) -> ChangeSet:
        """
        Retrieve a ChangeSet with all items prefetched.

        :param changeset_id: ChangeSet PK. Example: 1
        :return: ChangeSet with prefetched items.
        :raises ValueError: If not found.
        """
        raise NotImplementedError()

    def list(
        self,
        model_id: int,
        status: str | None = None,
        source: str | None = None,
        limit: int = 50,
    ) -> QuerySet[ChangeSet]:
        """
        List ChangeSets for a model with optional filters.

        :param model_id: YggdrasilModel PK. Example: 1
        :param status: Filter by status. Example: "pending"
        :param source: Filter by source. Example: "ratatosk"
        :param limit: Max results (default 50, server max 200). Example: 20
        :return: QuerySet of ChangeSet ordered by -created_at.
        """
        raise NotImplementedError()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_propose(
        self,
        operations: builtins.list[dict[str, Any]],
        source: str,
        allow_empty: bool,
    ) -> None:
        """Reject empty ops (unless allowed) and unknown sources."""
        if not operations and not allow_empty:
            _story(
                "ChangeSetService.propose",
                "validation",
                ops=len(operations),
                allow_empty=allow_empty,
            )
            _story(
                "ChangeSetService.propose",
                "error",
                reason="empty_operations",
                ops=len(operations),
                level=logging.ERROR,
            )
            msg = "operations must not be empty"
            raise ValueError(msg)
        valid_sources = {choice[0] for choice in ChangeSet.SOURCE_CHOICES}
        if source not in valid_sources:
            _story("ChangeSetService.propose", "validation", source=source)
            _story(
                "ChangeSetService.propose",
                "error",
                reason="invalid_source",
                source=source,
                level=logging.ERROR,
            )
            msg = f"Invalid source={source!r}; expected one of {sorted(valid_sources)}"
            raise ValueError(msg)
        _story(
            "ChangeSetService.propose",
            "validation",
            ops=len(operations),
            source=source,
        )

    def _get_model_or_raise(self, model_id: int) -> YggdrasilModel:
        """Load YggdrasilModel or raise ValueError with a model_not_found beat."""
        try:
            return YggdrasilModel.objects.get(pk=model_id)
        except YggdrasilModel.DoesNotExist as exc:
            msg = f"YggdrasilModel id={model_id} not found"
            _story(
                "ChangeSetService.propose",
                "error",
                reason="model_not_found",
                model_id=model_id,
                level=logging.ERROR,
            )
            raise ValueError(msg) from exc

    def _create_pending_changeset(
        self,
        model: YggdrasilModel,
        source: str,
        review_mode: str,
        run_id: str,
        munin_reasoning: str,
    ) -> ChangeSet:
        """Insert a pending ChangeSet row for propose()."""
        return ChangeSet.objects.create(
            model=model,
            source=source,
            status=ChangeSet.STATUS_PENDING,
            review_mode=review_mode,
            run_id=run_id,
            munin_reasoning=munin_reasoning,
        )

    def _create_operation_items(
        self,
        changeset: ChangeSet,
        operations: builtins.list[dict[str, Any]],
    ) -> None:
        """Persist ordered ChangeSetItem rows from propose() operations."""
        for order, op in enumerate(operations, start=1):
            ChangeSetItem.objects.create(
                changeset=changeset,
                order=order,
                op_type=op["op_type"],
                detail=op.get("detail") or {},
                confidence=float(op.get("confidence", 1.0)),
                status=ChangeSetItem.ITEM_STATUS_PENDING,
            )

    def _log_reject_learn_branch(self, learn: bool, reason: str) -> None:
        """Log whether reject() will create a MuninRule."""
        if learn and reason:
            _story(
                "ChangeSetService.reject",
                "branch",
                reason="learn_rule",
                learn=learn,
            )
            return
        _story(
            "ChangeSetService.reject",
            "branch",
            reason="no_rule",
            learn=learn,
            has_reason=bool(reason),
        )

    def _validate_do_other(
        self,
        item_ids: builtins.list[int],
        instructions: str,
    ) -> None:
        """Require at least one item id and non-empty instructions."""
        if not item_ids:
            _story(
                "ChangeSetService.do_other",
                "validation",
                item_ids_count=0,
            )
            _story(
                "ChangeSetService.do_other",
                "error",
                reason="empty_item_ids",
                level=logging.ERROR,
            )
            msg = "do_other requires at least one item_id"
            raise ValueError(msg)
        if not instructions.strip():
            _story(
                "ChangeSetService.do_other",
                "validation",
                instructions_len=0,
            )
            _story(
                "ChangeSetService.do_other",
                "error",
                reason="empty_instructions",
                level=logging.ERROR,
            )
            msg = "do_other requires non-empty instructions"
            raise ValueError(msg)
        _story(
            "ChangeSetService.do_other",
            "validation",
            item_ids_count=len(item_ids),
            instructions_len=len(instructions),
        )

    def _replan_rejected_items(
        self,
        changeset: ChangeSet,
        item_ids: builtins.list[int],
        instructions: str,
        user: User | None,
    ) -> builtins.list[int]:
        """Ask Munin to re-plan rejected items; return replacement ChangeSet PKs."""
        from yggdrasil.llm.base import ScriptedLLM
        from yggdrasil.munin.agent import MuninAgent

        agent = MuninAgent(
            llm=ScriptedLLM(responses=[f"Re-planned with: {instructions[:80]}"]),
            model_id=changeset.model_id,
            user_id=getattr(user, "pk", None),
        )
        replacement_ids: builtins.list[int] = []
        for item_id in item_ids:
            resp = agent.replan_operation(
                rejected_item_id=item_id,
                instructions=instructions,
            )
            if resp.changeset_id is not None:
                replacement_ids.append(resp.changeset_id)
        return replacement_ids

    def _apply_item(self, item: ChangeSetItem) -> None:
        """Apply a single ChangeSetItem to the graph inside the caller's transaction."""
        _story(
            "ChangeSetService._apply_item",
            "processing",
            item=item.pk,
            op=item.op_type,
            changeset=item.changeset_id,
        )
        model = item.changeset.model
        detail = item.detail or {}
        if item.op_type == ChangeSetItem.OP_ADD_ELEMENT:
            self._apply_add_element(model, item, detail)
        elif item.op_type == ChangeSetItem.OP_UPDATE_ELEMENT:
            self._apply_update_element(detail)
        elif item.op_type == ChangeSetItem.OP_DELETE_ELEMENT:
            self._apply_delete_element(detail)
        elif item.op_type == ChangeSetItem.OP_ADD_RELATIONSHIP:
            self._apply_add_relationship(model, detail)
        elif item.op_type == ChangeSetItem.OP_DELETE_RELATIONSHIP:
            self._apply_delete_relationship(detail)
        elif item.op_type == ChangeSetItem.OP_ADD_TO_DIAGRAM:
            self._apply_add_to_diagram(detail)
        else:
            msg = f"Unsupported op_type={item.op_type!r} on item={item.pk}"
            _story(
                "ChangeSetService._apply_item",
                "error",
                reason="unsupported_op",
                op=item.op_type,
                item=item.pk,
                level=logging.ERROR,
            )
            raise ValueError(msg)

    def _invert_item(self, item: ChangeSetItem) -> dict[str, Any]:
        """
        Produce the inverse operation dict[str, Any] for a rollback.

        :param item: Accepted ChangeSetItem to invert.
        :return: Dict with ``op_type``, ``detail``, ``confidence``.
        :raises ValueError: If ``op_type`` has no known inverse.
        """
        inverse_type = _INVERSE_OP_TYPES.get(item.op_type)
        if inverse_type is None:
            msg = f"Cannot invert unknown op_type={item.op_type!r} on item={item.pk}"
            raise ValueError(msg)
        detail = self._invert_detail(item.op_type, item.detail)
        _story(
            "ChangeSetService._invert_item",
            "processing",
            item=item.pk,
            op=item.op_type,
            inverse=inverse_type,
        )
        return {
            "op_type": inverse_type,
            "detail": detail,
            "confidence": item.confidence,
        }

    def _create_munin_rule(self, item: ChangeSetItem, reason: str, user: User | None) -> MuninRule:
        """Create a MuninRule from a rejected item and reason."""
        rule = MuninRule.objects.create(
            model=item.changeset.model,
            rule_text=reason,
            source_item=item,
            created_by=user,
            is_active=True,
        )
        _story(
            "ChangeSetService._create_munin_rule",
            "processing",
            rule_id=rule.pk,
            item=item.pk,
            user=getattr(user, "pk", None),
        )
        return rule

    def _get_applied_changeset(self, changeset_id: int) -> ChangeSet:
        """Load ChangeSet for rollback; require status=applied."""
        try:
            changeset = (
                ChangeSet.objects.select_related("model")
                .prefetch_related("items")
                .get(pk=changeset_id)
            )
        except ChangeSet.DoesNotExist as exc:
            msg = f"ChangeSet id={changeset_id} not found"
            _story(
                "ChangeSetService._get_applied_changeset",
                "error",
                reason="not_found",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise ValueError(msg) from exc
        if changeset.status != ChangeSet.STATUS_APPLIED:
            msg = (
                f"ChangeSet id={changeset_id} status={changeset.status!r}; "
                "rollback requires status='applied'"
            )
            _story(
                "ChangeSetService.rollback",
                "validation",
                reason="not_applied",
                changeset_id=changeset_id,
                status=changeset.status,
            )
            _story(
                "ChangeSetService._get_applied_changeset",
                "error",
                reason="not_applied",
                changeset_id=changeset_id,
                status=changeset.status,
                level=logging.ERROR,
            )
            raise ValueError(msg)
        _story(
            "ChangeSetService.rollback",
            "validation",
            status=changeset.status,
            changeset_id=changeset_id,
        )
        return changeset

    def _accepted_items(self, changeset: ChangeSet) -> builtins.list[ChangeSetItem]:
        """Return accepted items in apply order (order ascending)."""
        return [
            item
            for item in changeset.items.all()
            if item.status == ChangeSetItem.ITEM_STATUS_ACCEPTED
        ]

    def _create_rollback_changeset(
        self,
        source_cs: ChangeSet,
        accepted: builtins.list[ChangeSetItem],
    ) -> ChangeSet:
        """Create pending rollback ChangeSet with inverse ops (reverse apply order)."""
        rollback_cs = ChangeSet.objects.create(
            model=source_cs.model,
            source=ChangeSet.SOURCE_ROLLBACK,
            status=ChangeSet.STATUS_PENDING,
            review_mode=source_cs.review_mode,
            run_id=f"rollback-{source_cs.pk}",
            munin_reasoning=f"Rollback of ChangeSet#{source_cs.pk}",
        )
        # Invert in reverse order so deletes precede recreates when applied later.
        for order, item in enumerate(reversed(accepted), start=1):
            inverse = self._invert_item(item)
            ChangeSetItem.objects.create(
                changeset=rollback_cs,
                order=order,
                op_type=inverse["op_type"],
                detail=inverse["detail"],
                confidence=inverse["confidence"],
                status=ChangeSetItem.ITEM_STATUS_PENDING,
            )
        return rollback_cs

    def _invert_detail(self, op_type: str, detail: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of detail with update_element field pairs swapped."""
        inverted = dict(detail)
        if op_type != ChangeSetItem.OP_UPDATE_ELEMENT:
            return inverted
        fields = detail.get("fields", {})
        swapped: dict[str, Any] = {}
        for field_name, pair in fields.items():
            if isinstance(pair, list | tuple) and len(pair) == 2:
                swapped[field_name] = [pair[1], pair[0]]
            else:
                swapped[field_name] = pair
        inverted["fields"] = swapped
        return inverted

    def _get_pending_changeset(self, changeset_id: int) -> ChangeSet:
        """Load ChangeSet for approve/reject; reject already-applied."""
        try:
            changeset = (
                ChangeSet.objects.select_related("model")
                .prefetch_related("items")
                .get(pk=changeset_id)
            )
        except ChangeSet.DoesNotExist as exc:
            msg = f"ChangeSet id={changeset_id} not found"
            _story(
                "ChangeSetService._get_pending_changeset",
                "error",
                reason="not_found",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise ValueError(msg) from exc
        if changeset.status == ChangeSet.STATUS_APPLIED:
            msg = f"ChangeSet id={changeset_id} already applied"
            _story(
                "ChangeSetService._get_pending_changeset",
                "error",
                reason="already_applied",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise ValueError(msg)
        return changeset

    def _select_pending_items(
        self,
        changeset: ChangeSet,
        item_ids: builtins.list[int] | None,
    ) -> builtins.list[ChangeSetItem]:
        """Return pending items to process; optionally filter by PK list."""
        pending = [
            item
            for item in changeset.items.all()
            if item.status == ChangeSetItem.ITEM_STATUS_PENDING
        ]
        if item_ids is None:
            _story(
                "ChangeSetService._select_pending_items",
                "branch",
                reason="all_pending",
                selected_count=len(pending),
                changeset_id=changeset.pk,
            )
            return pending
        wanted = set(item_ids)
        selected = [item for item in pending if item.pk in wanted]
        missing = wanted - {item.pk for item in selected}
        if missing:
            msg = f"Pending items not found on ChangeSet {changeset.pk}: {sorted(missing)}"
            _story(
                "ChangeSetService._select_pending_items",
                "error",
                reason="missing_ids",
                missing=sorted(missing),
                changeset_id=changeset.pk,
                level=logging.ERROR,
            )
            raise ValueError(msg)
        _story(
            "ChangeSetService._select_pending_items",
            "branch",
            reason="item_ids_filter",
            selected_count=len(selected),
            changeset_id=changeset.pk,
        )
        return selected

    def _finalize_changeset_status(self, changeset: ChangeSet, user: User | None) -> None:
        """Set applied/rejected when no pending items remain; else leave status."""
        remaining = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).count()
        accepted = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_ACCEPTED).count()
        rejected = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_REJECTED).count()
        if remaining > 0:
            _story(
                "ChangeSetService._finalize_changeset_status",
                "branch",
                reason="still_pending",
                remaining=remaining,
                accepted=accepted,
                rejected=rejected,
                changeset_id=changeset.pk,
            )
            return
        if accepted > 0:
            changeset.status = ChangeSet.STATUS_APPLIED
            changeset.applied_at = timezone.now()
            changeset.applied_by = user
            changeset.save(update_fields=["status", "applied_at", "applied_by"])
            _story(
                "ChangeSetService._finalize_changeset_status",
                "branch",
                reason="applied",
                accepted=accepted,
                rejected=rejected,
                changeset_id=changeset.pk,
            )
            return
        changeset.status = ChangeSet.STATUS_REJECTED
        changeset.save(update_fields=["status"])
        _story(
            "ChangeSetService._finalize_changeset_status",
            "branch",
            reason="rejected",
            accepted=accepted,
            rejected=rejected,
            changeset_id=changeset.pk,
        )

    def _apply_add_element(
        self, model: YggdrasilModel, item: ChangeSetItem, detail: dict[str, Any]
    ) -> None:
        """Create an Element from an add_element detail payload."""
        name = detail.get("name")
        if not name:
            msg = f"add_element item={item.pk} missing detail.name"
            raise ValueError(msg)
        stereotype = self._get_or_create_stereotype(
            model, detail.get("stereotype_slug", "container"), is_edge=False
        )
        package = self._get_or_create_package(model, detail.get("package_slug", "technology"))
        element, created = Element.objects.get_or_create(
            model=model,
            slug=slugify(name),
            defaults={
                "name": name,
                "stereotype": stereotype,
                "package": package,
                "properties": detail.get("properties", {}),
                "owner": detail.get("owner", ""),
                "source": Element.SOURCE_RATATOSK,
                "confidence": item.confidence,
            },
        )
        item.detail = {**detail, "element_id": element.pk}
        created_reason = "created" if created else "existing_element"
        _story(
            "ChangeSetService._apply_add_element",
            "processing",
            item=item.pk,
            element_id=element.pk,
            created=created,
        )
        _story(
            "ChangeSetService._apply_add_element",
            "branch",
            reason=created_reason,
            element_id=element.pk,
            item=item.pk,
        )

    def _apply_update_element(self, detail: dict[str, Any]) -> None:
        """Apply field updates from update_element detail."""
        element_id = detail.get("element_id")
        if element_id is None:
            msg = "update_element missing element_id"
            raise ValueError(msg)
        element = Element.objects.get(pk=element_id)
        for field_name, pair in (detail.get("fields") or {}).items():
            if isinstance(pair, list | tuple) and len(pair) == 2:
                setattr(element, field_name, pair[1])
        element.save()

    def _apply_delete_element(self, detail: dict[str, Any]) -> None:
        """Delete element referenced by delete_element detail."""
        element_id = detail.get("element_id")
        if element_id is None:
            msg = "delete_element missing element_id"
            raise ValueError(msg)
        Element.objects.filter(pk=element_id).delete()

    def _apply_add_relationship(self, model: YggdrasilModel, detail: dict[str, Any]) -> None:
        """Create a Relationship from add_relationship detail."""
        source_id = detail.get("source_id")
        target_id = detail.get("target_id")
        if not source_id:
            source_id = self._resolve_element_id(
                model,
                detail.get("source_name"),
                detail.get("source_slug"),
            )
        if not target_id:
            target_id = self._resolve_element_id(
                model,
                detail.get("target_name"),
                detail.get("target_slug"),
            )
        stereotype = self._get_or_create_stereotype(
            model, detail.get("stereotype_slug", "depends_on"), is_edge=True
        )
        _story(
            "ChangeSetService._apply_add_relationship",
            "processing",
            source_id=source_id,
            target_id=target_id,
            stereotype=stereotype.slug,
        )
        Relationship.objects.get_or_create(
            model=model,
            source_id=source_id,
            target_id=target_id,
            stereotype=stereotype,
            defaults={"properties": detail.get("properties", {})},
        )

    def _resolve_element_id(
        self,
        model: YggdrasilModel,
        name: str | None,
        slug: str | None,
    ) -> int:
        """Resolve element PK by name or slug within model."""
        qs = Element.objects.filter(model=model)
        if slug:
            el = qs.filter(slug=slug).first()
            if el:
                _story(
                    "ChangeSetService._resolve_element_id",
                    "branch",
                    reason="by_slug",
                    slug=slug,
                    element_id=el.pk,
                )
                return el.pk
        if name:
            el = qs.filter(name=name).first()
            if el:
                _story(
                    "ChangeSetService._resolve_element_id",
                    "branch",
                    reason="by_name",
                    name=name,
                    element_id=el.pk,
                )
                return el.pk
        msg = f"Element not found for relationship: name={name!r} slug={slug!r}"
        _story(
            "ChangeSetService._resolve_element_id",
            "error",
            reason="not_found",
            name=name,
            slug=slug,
            level=logging.ERROR,
        )
        raise ValueError(msg)

    def _apply_delete_relationship(self, detail: dict[str, Any]) -> None:
        """Delete relationship referenced by delete_relationship detail."""
        rel_id = detail.get("relationship_id")
        if rel_id is None:
            msg = "delete_relationship missing relationship_id"
            raise ValueError(msg)
        Relationship.objects.filter(pk=rel_id).delete()

    def _apply_add_to_diagram(self, detail: dict[str, Any]) -> None:
        """Attach element to diagram via M2M."""
        element = Element.objects.get(pk=detail["element_id"])
        diagram = Diagram.objects.get(pk=detail["diagram_id"])
        element.diagrams.add(diagram)

    def _get_or_create_stereotype(
        self, model: YggdrasilModel, slug: str, *, is_edge: bool
    ) -> Stereotype:
        """
        Resolve stereotype from the Model's Metamodel catalog.

        Does not invent catalog rows — unknown slugs raise ValueError.
        """
        try:
            return Stereotype.objects.get(
                metamodel=model.metamodel,
                slug=slug,
                is_edge=is_edge,
            )
        except Stereotype.DoesNotExist as exc:
            kind = "edge" if is_edge else "element"
            msg = (
                f"Unknown {kind} stereotype {slug!r} on metamodel "
                f"{model.metamodel.slug!r}. Add it in Django admin."
            )
            logger.warning(
                "ChangeSetService._get_or_create_stereotype | error | reason=unknown_stereotype %s",
                msg,
            )
            raise ValueError(msg) from exc

    def _get_or_create_package(self, model: YggdrasilModel, slug: str) -> Package:
        """
        Resolve package from the Model's Metamodel catalog.

        Does not invent catalog rows — unknown slugs raise ValueError.
        """
        try:
            return Package.objects.get(metamodel=model.metamodel, slug=slug)
        except Package.DoesNotExist as exc:
            msg = (
                f"Unknown package {slug!r} on metamodel {model.metamodel.slug!r}. "
                "Add it in Django admin."
            )
            logger.warning(
                "ChangeSetService._get_or_create_package | error | reason=unknown_package %s",
                msg,
            )
            raise ValueError(msg) from exc
