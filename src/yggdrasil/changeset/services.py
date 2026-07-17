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
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem, MuninRule
from yggdrasil.graph.models import Diagram, Element, Package, Relationship, Stereotype

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from django.db.models import QuerySet

logger = logging.getLogger("yggdrasil.changeset")

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
        operations: list[dict],
        munin_reasoning: str = "",
        run_id: str = "",
        review_mode: str = ChangeSet.REVIEW_MANUAL,
        user: User | None = None,
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
        :return: Created ChangeSet with status="pending".
        :raises ValueError: If operations is empty or source is invalid.

        :Example:

        >>> cs = svc.propose(model_id=1, source="mcp",
        ...     operations=[{"op_type": "add_element", "detail": {...}, "confidence": 0.9}])
        >>> cs.status
        'pending'
        """
        raise NotImplementedError()

    def approve(
        self,
        changeset_id: int,
        item_ids: list[int] | None = None,
        user: User | None = None,
    ) -> ChangeSet:
        """
        Apply all (or specified) pending operations in a ChangeSet to the graph.

        Runs inside a single DB transaction — all-or-nothing per call.
        If ``item_ids`` is provided, only those items are applied;
        others remain pending for a subsequent call.

        :param changeset_id: ChangeSet PK. Example: 1
        :param item_ids: Optional list of ChangeSetItem PKs to apply.
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
        user_label = getattr(user, "pk", None)
        logger.info(
            "approve | changeset_id=%s item_ids=%s user=%s",
            changeset_id,
            item_ids,
            user_label,
        )
        with transaction.atomic():
            changeset = self._get_pending_changeset(changeset_id)
            targets = self._select_pending_items(changeset, item_ids)
            for item in targets:
                self._apply_item(item)
                item.status = ChangeSetItem.ITEM_STATUS_ACCEPTED
                item.save(update_fields=["status", "detail"])
            self._finalize_changeset_status(changeset, user)
        logger.info(
            "approve | changeset_id=%s applied_count=%s status=%s user=%s",
            changeset.pk,
            len(targets),
            changeset.status,
            user_label,
        )
        return changeset

    def reject(
        self,
        changeset_id: int,
        item_ids: list[int] | None = None,
        reason: str = "",
        user: User | None = None,
        learn: bool = True,
    ) -> ChangeSet:
        """
        Reject all (or specified) pending operations; optionally learn from the reason.

        If ``reason`` is provided and ``learn=True``, a MuninRule is created
        so Munin avoids the same operation in future runs.

        :param changeset_id: ChangeSet PK. Example: 1
        :param item_ids: Optional list of ChangeSetItem PKs to reject.
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
        raise NotImplementedError()

    def do_other(
        self,
        changeset_id: int,
        item_ids: list[int],
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
        raise NotImplementedError()

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
        user_label = getattr(user, "pk", None)
        logger.info(
            "rollback | changeset_id=%s user=%s",
            changeset_id,
            user_label,
        )
        with transaction.atomic():
            source_cs = self._get_applied_changeset(changeset_id)
            accepted = self._accepted_items(source_cs)
            rollback_cs = self._create_rollback_changeset(source_cs, accepted)
        logger.info(
            "rollback | created rollback_id=%s reversing=%s from changeset_id=%s user=%s",
            rollback_cs.pk,
            len(accepted),
            changeset_id,
            user_label,
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
    ) -> QuerySet:
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

    def _apply_item(self, item: ChangeSetItem) -> None:
        """Apply a single ChangeSetItem to the graph inside the caller's transaction."""
        logger.info(
            "_apply_item | item=%s op=%s changeset=%s",
            item.pk,
            item.op_type,
            item.changeset_id,
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
            raise ValueError(msg)

    def _invert_item(self, item: ChangeSetItem) -> dict:
        """
        Produce the inverse operation dict for a rollback.

        :param item: Accepted ChangeSetItem to invert.
        :return: Dict with ``op_type``, ``detail``, ``confidence``.
        :raises ValueError: If ``op_type`` has no known inverse.
        """
        inverse_type = _INVERSE_OP_TYPES.get(item.op_type)
        if inverse_type is None:
            msg = f"Cannot invert unknown op_type={item.op_type!r} on item={item.pk}"
            raise ValueError(msg)
        detail = self._invert_detail(item.op_type, item.detail)
        logger.info(
            "_invert_item | item=%s op=%s → %s",
            item.pk,
            item.op_type,
            inverse_type,
        )
        return {
            "op_type": inverse_type,
            "detail": detail,
            "confidence": item.confidence,
        }

    def _create_munin_rule(self, item: ChangeSetItem, reason: str, user: User | None) -> MuninRule:
        """Create a MuninRule from a rejected item and reason."""
        raise NotImplementedError()

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
            raise ValueError(msg) from exc
        if changeset.status != ChangeSet.STATUS_APPLIED:
            msg = (
                f"ChangeSet id={changeset_id} status={changeset.status!r}; "
                "rollback requires status='applied'"
            )
            raise ValueError(msg)
        return changeset

    def _accepted_items(self, changeset: ChangeSet) -> list[ChangeSetItem]:
        """Return accepted items in apply order (order ascending)."""
        return [
            item
            for item in changeset.items.all()
            if item.status == ChangeSetItem.ITEM_STATUS_ACCEPTED
        ]

    def _create_rollback_changeset(
        self,
        source_cs: ChangeSet,
        accepted: list[ChangeSetItem],
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

    def _invert_detail(self, op_type: str, detail: dict) -> dict:
        """Return a copy of detail with update_element field pairs swapped."""
        inverted = dict(detail)
        if op_type != ChangeSetItem.OP_UPDATE_ELEMENT:
            return inverted
        fields = detail.get("fields", {})
        swapped: dict = {}
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
            raise ValueError(msg) from exc
        if changeset.status == ChangeSet.STATUS_APPLIED:
            msg = f"ChangeSet id={changeset_id} already applied"
            raise ValueError(msg)
        return changeset

    def _select_pending_items(
        self,
        changeset: ChangeSet,
        item_ids: list[int] | None,
    ) -> list[ChangeSetItem]:
        """Return pending items to process; optionally filter by PK list."""
        pending = [
            item
            for item in changeset.items.all()
            if item.status == ChangeSetItem.ITEM_STATUS_PENDING
        ]
        if item_ids is None:
            return pending
        wanted = set(item_ids)
        selected = [item for item in pending if item.pk in wanted]
        missing = wanted - {item.pk for item in selected}
        if missing:
            msg = f"Pending items not found on ChangeSet {changeset.pk}: {sorted(missing)}"
            raise ValueError(msg)
        return selected

    def _finalize_changeset_status(self, changeset: ChangeSet, user: User | None) -> None:
        """Set applied/rejected when no pending items remain; else leave status."""
        remaining = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).count()
        if remaining > 0:
            logger.info(
                "_finalize_changeset_status | changeset_id=%s still_pending=%s",
                changeset.pk,
                remaining,
            )
            return
        accepted = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_ACCEPTED).count()
        if accepted > 0:
            changeset.status = ChangeSet.STATUS_APPLIED
            changeset.applied_at = timezone.now()
            changeset.applied_by = user
            changeset.save(update_fields=["status", "applied_at", "applied_by"])
        else:
            changeset.status = ChangeSet.STATUS_REJECTED
            changeset.save(update_fields=["status"])

    def _apply_add_element(self, model, item: ChangeSetItem, detail: dict) -> None:
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
        logger.info(
            "_apply_add_element | item=%s element_id=%s created=%s",
            item.pk,
            element.pk,
            created,
        )

    def _apply_update_element(self, detail: dict) -> None:
        """Apply field updates from update_element detail."""
        element_id = detail.get("element_id")
        element = Element.objects.get(pk=element_id)
        for field_name, pair in (detail.get("fields") or {}).items():
            if isinstance(pair, list | tuple) and len(pair) == 2:
                setattr(element, field_name, pair[1])
        element.save()

    def _apply_delete_element(self, detail: dict) -> None:
        """Delete element referenced by delete_element detail."""
        element_id = detail.get("element_id")
        Element.objects.filter(pk=element_id).delete()

    def _apply_add_relationship(self, model, detail: dict) -> None:
        """Create a Relationship from add_relationship detail."""
        stereotype = self._get_or_create_stereotype(
            model, detail.get("stereotype_slug", "depends_on"), is_edge=True
        )
        Relationship.objects.get_or_create(
            model=model,
            source_id=detail["source_id"],
            target_id=detail["target_id"],
            stereotype=stereotype,
            defaults={"properties": detail.get("properties", {})},
        )

    def _apply_delete_relationship(self, detail: dict) -> None:
        """Delete relationship referenced by delete_relationship detail."""
        Relationship.objects.filter(pk=detail.get("relationship_id")).delete()

    def _apply_add_to_diagram(self, detail: dict) -> None:
        """Attach element to diagram via M2M."""
        element = Element.objects.get(pk=detail["element_id"])
        diagram = Diagram.objects.get(pk=detail["diagram_id"])
        element.diagrams.add(diagram)

    def _get_or_create_stereotype(self, model, slug: str, *, is_edge: bool) -> Stereotype:
        """Return stereotype for model+slug, creating a minimal stub if needed."""
        stereotype, _ = Stereotype.objects.get_or_create(
            model=model,
            slug=slug,
            defaults={"name": slug.replace("-", " ").title(), "is_edge": is_edge},
        )
        return stereotype

    def _get_or_create_package(self, model, slug: str) -> Package:
        """Return package for model+slug, creating a minimal stub if needed."""
        package, _ = Package.objects.get_or_create(
            model=model,
            slug=slug,
            defaults={"name": slug.replace("-", " ").title()},
        )
        return package
