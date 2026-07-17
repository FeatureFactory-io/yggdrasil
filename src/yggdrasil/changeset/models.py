"""
ChangeSet domain models: durable audit trail for all graph writes.

All writes to the graph (human, Ratatosk, MCP) go through here —
never directly via ORM (SAO.md §1, §4, §7 — ChangeSet atomicity).

Bounded context: `changeset` (SAO.md §1).
Dependency rules: changeset → graph only.

JSONB columns (SAO.md §4):
  - ChangeSetItem.detail    — operation-specific payload (add/update/delete)
  - MuninRule.rule_text     — append-only LEARNED rules for Munin's BASE prompt
"""

from __future__ import annotations

import logging
from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models

from yggdrasil.graph.models import YggdrasilModel

logger = logging.getLogger("yggdrasil.changeset")


class ChangeSet(models.Model):
    """
    An ordered batch of graph operations produced by Ratatosk, Munin, or a human.

    A ChangeSet is the unit of review: it is either applied (all ops committed)
    or rejected (all ops discarded). Partial applies are modelled via
    ``ChangeSetItem.status`` — individual items may be accepted or rejected
    before the ChangeSet is finalised.

    ``review_mode`` mirrors the YggdrasilModel setting at the time of creation
    so that historical ChangeSets preserve their original approval policy.

    :Example:

    >>> cs = ChangeSet.objects.create(
    ...     model=model, source=ChangeSet.SOURCE_RATATOSK,
    ...     run_id="run-003", review_mode=ChangeSet.REVIEW_MANUAL,
    ... )
    """

    STATUS_PENDING = "pending"
    STATUS_APPLIED = "applied"
    STATUS_REJECTED = "rejected"
    STATUS_FAILED = "failed"
    STATUS_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPLIED, "Applied"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_FAILED, "Failed"),
    ]

    SOURCE_RATATOSK = "ratatosk"
    SOURCE_HUMAN = "human"
    SOURCE_MCP = "mcp"
    SOURCE_ROLLBACK = "rollback"
    SOURCE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (SOURCE_RATATOSK, "Ratatosk"),
        (SOURCE_HUMAN, "Human"),
        (SOURCE_MCP, "MCP"),
        (SOURCE_ROLLBACK, "Rollback"),
    ]

    REVIEW_AUTO = "auto"
    REVIEW_MANUAL = "manual"
    REVIEW_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (REVIEW_AUTO, "Auto"),
        (REVIEW_MANUAL, "Manual"),
    ]

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="changesets",
    )
    run_id = models.CharField(max_length=50, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_HUMAN)
    review_mode = models.CharField(max_length=10, choices=REVIEW_CHOICES, default=REVIEW_MANUAL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    munin_reasoning = models.TextField(blank=True)
    applied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applied_changesets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    applied_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return f"ChangeSet#{self.pk} [{self.run_id}] {self.status}"

    @property
    def operations_count(self) -> int:
        """Return the total number of ChangeSetItems."""
        return self.items.count()


class ChangeSetItem(models.Model):
    """
    A single graph operation within a ChangeSet.

    ``op_type`` determines how ``detail`` (JSONB) is interpreted:
      - ``add_element``: detail = {name, stereotype_slug, package_slug, properties, owner}
      - ``update_element``: detail = {element_id, fields: {field: [old, new], ...}}
      - ``delete_element``: detail = {element_id}
      - ``add_relationship``: detail = {source_id, target_id, stereotype_slug, properties}
      - ``delete_relationship``: detail = {relationship_id}
      - ``add_to_diagram``: detail = {element_id, diagram_id}

    ``confidence`` is 0.0-1.0, set by Ratatosk or Munin.

    :Example:

    >>> item = ChangeSetItem.objects.create(
    ...     changeset=cs, op_type=ChangeSetItem.OP_ADD_ELEMENT, order=1,
    ...     detail={"name": "Notification Service", "stereotype_slug": "container"},
    ...     confidence=0.92,
    ... )
    """

    OP_ADD_ELEMENT = "add_element"
    OP_UPDATE_ELEMENT = "update_element"
    OP_DELETE_ELEMENT = "delete_element"
    OP_ADD_RELATIONSHIP = "add_relationship"
    OP_DELETE_RELATIONSHIP = "delete_relationship"
    OP_ADD_TO_DIAGRAM = "add_to_diagram"
    OP_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (OP_ADD_ELEMENT, "Add Element"),
        (OP_UPDATE_ELEMENT, "Update Element"),
        (OP_DELETE_ELEMENT, "Delete Element"),
        (OP_ADD_RELATIONSHIP, "Add Relationship"),
        (OP_DELETE_RELATIONSHIP, "Delete Relationship"),
        (OP_ADD_TO_DIAGRAM, "Add to Diagram"),
    ]

    ITEM_STATUS_PENDING = "pending"
    ITEM_STATUS_ACCEPTED = "accepted"
    ITEM_STATUS_REJECTED = "rejected"
    ITEM_STATUS_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (ITEM_STATUS_PENDING, "Pending"),
        (ITEM_STATUS_ACCEPTED, "Accepted"),
        (ITEM_STATUS_REJECTED, "Rejected"),
    ]

    changeset = models.ForeignKey(
        ChangeSet,
        on_delete=models.CASCADE,
        related_name="items",
    )
    order = models.PositiveIntegerField(default=0)
    op_type = models.CharField(max_length=30, choices=OP_CHOICES)
    detail = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20, choices=ITEM_STATUS_CHOICES, default=ITEM_STATUS_PENDING
    )
    confidence = models.FloatField(default=1.0)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["order"]
        unique_together: ClassVar[list[tuple[str, str]]] = [("changeset", "order")]

    def __str__(self) -> str:
        return f"CS#{self.changeset_id} op{self.order}: {self.op_type}"


class MuninRule(models.Model):
    """
    An append-only LEARNED rule prepended to Munin's BASE prompt.

    Rules are created when a ChangeSetItem is rejected with an explanatory
    reason, or when Marcus uses "Do Other" with instructions.  They are
    injected into the Munin Prompt Stack Layer 1 (Foundation) so Munin
    learns from human corrections over time.

    Never delete rules — mark ``is_active=False`` to suppress them.

    :Example:

    >>> rule = MuninRule.objects.create(
    ...     model=model,
    ...     rule_text="Code diagram is for repository structure, not runtime services",
    ...     source_item=rejected_item,
    ... )
    """

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="munin_rules",
    )
    rule_text = models.TextField()
    source_item = models.ForeignKey(
        ChangeSetItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learned_rules",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_munin_rules",
    )

    class Meta:
        ordering: ClassVar[list[str]] = ["created_at"]

    def __str__(self) -> str:
        return f"MuninRule#{self.pk}: {self.rule_text[:60]}..."
