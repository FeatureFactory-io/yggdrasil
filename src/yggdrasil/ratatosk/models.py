"""
Ratatosk domain models: NER run history and agent state.

RataskRun records every CLI invocation. The blackboard JSONB column
stores the agent's "letter to future self" across steps (SAO.md §17.4).

Bounded context: `ratatosk` (SAO.md §1).
Dependency rules: ratatosk → graph, changeset, llm.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from django.contrib.auth.models import User
from django.db import models

from yggdrasil.graph.models import YggdrasilModel

logger = logging.getLogger("yggdrasil.ratatosk")


class RataskRun(models.Model):
    """
    A single Ratatosk bootstrap or update run.

    The run lifecycle: created → running → complete|failed.
    ``blackboard`` (JSONB) persists agent state between steps so the agent
    can resume after interruption (SAO.md §17.4 — Agent Blackboard).

    :Example:

    >>> run = RataskRun.objects.create(
    ...     model=model, triggered_by=user,
    ...     run_id="run-003", repo_path="./repo",
    ... )
    """

    STATUS_RUNNING = "running"
    STATUS_COMPLETE = "complete"
    STATUS_FAILED = "failed"
    STATUS_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (STATUS_RUNNING, "Running"),
        (STATUS_COMPLETE, "Complete"),
        (STATUS_FAILED, "Failed"),
    ]

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="ratatosk_runs",
    )
    run_id = models.CharField(max_length=50, unique=True)
    repo_path = models.CharField(max_length=500)
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RUNNING)
    blackboard = models.JSONField(default=dict)
    delta_summary = models.JSONField(default=dict)
    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratatosk_runs",
    )
    changeset = models.ForeignKey(
        "changeset.ChangeSet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratatosk_runs",
    )
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return f"RataskRun({self.run_id}) [{self.status}]"
