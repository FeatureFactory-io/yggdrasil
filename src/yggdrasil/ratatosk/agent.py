"""
Ratatosk NER agent: code-scan → delta buckets → Munin handoff (SAO.md §17.6).

Assembly profile: Field/Batch Specialist (SAO.md §17.2).
Modules active: LLM Port, Prompt Stack, Tool Surface, Agent Loop, Plan & Steps,
Worker, Agent Blackboard.

The agent is invoked via CLI (``ratatosk bootstrap``) and runs as a Celery task.
It does NOT run in a web request — never import this in Django views.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yggdrasil.llm.base import BaseLLM
    from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.ratatosk.agent")


@dataclass
class DeltaBuckets:
    """
    Candidate graph changes produced by NER scan, pre-bucketed by operation type.

    :Example:

    >>> buckets = DeltaBuckets(to_add=[...], to_update=[...], to_delete=[...])
    """

    to_add: list[dict] = field(default_factory=list)
    to_update: list[dict] = field(default_factory=list)
    to_delete: list[dict] = field(default_factory=list)
    unchanged: list[dict] = field(default_factory=list)

    @property
    def total_ops(self) -> int:
        """Total number of planned operations (excluding unchanged)."""
        return len(self.to_add) + len(self.to_update) + len(self.to_delete)


class RataskAgent:
    """
    Ratatosk NER field agent: scans a repository and produces delta buckets.

    Called by the Celery task; never called directly from web views.
    Uses ScriptedLLM in integration tests (LLM_PROVIDER=scripted env).

    :Example:

    >>> agent = RataskAgent(llm=scripted_llm, run=ratask_run)
    >>> buckets = agent.execute()
    """

    def __init__(self, llm: BaseLLM, run: RataskRun) -> None:
        """
        :param llm: LLM client to use for NER extraction.
        :param run: RataskRun record that tracks this execution.
        """
        self._llm = llm
        self._run = run
        logger.info(
            "RataskAgent: initialised | run_id=%s repo=%s",
            run.run_id,
            run.repo_path,
        )

    def execute(self) -> DeltaBuckets:
        """
        Scan the repository and produce delta buckets.

        Reads existing model state via MCP query tools, runs NER extraction
        with the LLM, reconciles against the current model, and returns
        pre-bucketed deltas for Munin to process.

        :return: DeltaBuckets with to_add, to_update, to_delete, unchanged.
        :raises RuntimeError: If repo_path is not accessible.
        :raises LLMError: If LLM call fails.
        """
        raise NotImplementedError()

    def _read_existing_model(self) -> dict:
        """Fetch current model state via internal service call."""
        raise NotImplementedError()

    def _scan_repository(self, repo_path: str) -> list[dict]:
        """Walk the repository and extract raw NER candidates using the LLM."""
        raise NotImplementedError()

    def _reconcile(self, candidates: list[dict], existing: dict) -> DeltaBuckets:
        """Diff candidates against existing model to produce delta buckets."""
        raise NotImplementedError()

    def _update_blackboard(self, step: str, data: dict) -> None:
        """Persist agent state to RataskRun.blackboard JSONB."""
        raise NotImplementedError()

    def _apply_confidence_threshold(
        self, buckets: DeltaBuckets, threshold: float
    ) -> tuple[DeltaBuckets, DeltaBuckets]:
        """
        Split buckets into above-threshold (auto-apply) and below-threshold (queue).

        :param buckets: Full delta buckets.
        :param threshold: Confidence threshold. Example: 0.80
        :return: (above_threshold, below_threshold) DeltaBuckets pair.
        """
        raise NotImplementedError()
