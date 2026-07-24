"""
Handoff ports: push delta buckets to Munin via ChangeSet (local ORM or MCP).

Production CLI uses ``McpHandoffPort``. Pytest / AT may inject
``LocalOrmHandoffPort`` or an in-process MCP tool client.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.graph.models import YggdrasilModel
from yggdrasil.ratatosk.models import RataskRun

logger = logging.getLogger("yggdrasil.ratatosk.handoff")

_service = ChangeSetService()
DEFAULT_CONFIDENCE_THRESHOLD = 0.80


@runtime_checkable
class HandoffPort(Protocol):
    """Submit Ratatosk operations and record the run."""

    def propose(
        self,
        *,
        model_slug: str,
        operations: list[dict[str, Any]],
        munin_reasoning: str,
        run_id: str,
        allow_empty: bool,
        confidence_threshold: float,
        user: Any = None,
        handoff_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Propose a ChangeSet; return dict with changeset_id, status, counts."""
        ...

    def record_run(
        self,
        *,
        model_slug: str,
        run_id: str,
        repo_path: str,
        instructions: str,
        blackboard: dict[str, Any],
        changeset_id: int | None,
        status: str,
        trigger: str,
        delta_summary: dict[str, Any],
        user: Any = None,
    ) -> dict[str, Any]:
        """Persist RataskRun blackboard / linkage."""
        ...


class LocalOrmHandoffPort:
    """In-process ORM handoff for AT / legacy adapter (not production CLI)."""

    def propose(
        self,
        *,
        model_slug: str,
        operations: list[dict[str, Any]],
        munin_reasoning: str,
        run_id: str,
        allow_empty: bool,
        confidence_threshold: float,
        user: Any = None,
        handoff_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create ChangeSet via ChangeSetService and auto-apply above threshold."""
        model = YggdrasilModel.objects.get(slug__iexact=model_slug)
        changeset = _service.propose(
            model_id=model.pk,
            source=ChangeSet.SOURCE_RATATOSK,
            operations=operations,
            munin_reasoning=munin_reasoning,
            run_id=run_id,
            review_mode=ChangeSet.REVIEW_MANUAL,
            user=user,
            allow_empty=allow_empty,
        )
        auto_ids = [
            item.pk
            for item in changeset.items.all()
            if float(item.confidence) >= confidence_threshold
        ]
        if auto_ids:
            changeset = _service.approve(changeset_id=changeset.pk, item_ids=auto_ids, user=user)
        applied = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_ACCEPTED).count()
        pending = changeset.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).count()
        logger.info(
            "LocalOrmHandoffPort.propose | changeset_id=%s applied=%s pending=%s",
            changeset.pk,
            applied,
            pending,
        )
        return {
            "changeset_id": changeset.pk,
            "status": changeset.status,
            "applied_count": applied,
            "pending_count": pending,
            "run_url": f"https://yggdrasil.local/ratatosk-runs/{run_id}",
            "operations_count": changeset.items.count(),
        }

    def record_run(
        self,
        *,
        model_slug: str,
        run_id: str,
        repo_path: str,
        instructions: str,
        blackboard: dict[str, Any],
        changeset_id: int | None,
        status: str,
        trigger: str,
        delta_summary: dict[str, Any],
        user: Any = None,
    ) -> dict[str, Any]:
        """Update existing RataskRun created by the agent orchestrator."""
        run = RataskRun.objects.get(run_id=run_id)
        board = dict(blackboard or {})
        board.setdefault("trigger", trigger)
        run.blackboard = board
        run.delta_summary = delta_summary or {}
        run.status = status
        if changeset_id is not None:
            run.changeset_id = changeset_id
        run.save()
        logger.info(
            "LocalOrmHandoffPort.record_run | run_id=%s changeset_id=%s",
            run_id,
            changeset_id,
        )
        return {
            "run_id": run.run_id,
            "changeset_id": run.changeset_id,
            "status": run.status,
        }


class McpHandoffPort:
    """Handoff via MCP ``propose_changeset`` + ``record_ratatosk_run``."""

    def __init__(self, client: Any) -> None:
        """
        :param client: Object with ``call_tool(name, arguments) -> dict``.
        """
        self._client = client

    def propose(
        self,
        *,
        model_slug: str,
        operations: list[dict[str, Any]],
        munin_reasoning: str,
        run_id: str,
        allow_empty: bool,
        confidence_threshold: float,
        user: Any = None,
        handoff_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call MCP propose_changeset (server enforces token scope)."""
        logger.info(
            "McpHandoffPort.propose | model=%s ops=%s run_id=%s handoff_keys=%s",
            model_slug,
            len(operations),
            run_id,
            sorted((handoff_context or {}).keys()),
        )
        payload: dict[str, Any] = {
            "model": model_slug,
            "operations": operations,
            "source": ChangeSet.SOURCE_RATATOSK,
            "munin_reasoning": munin_reasoning,
            "run_id": run_id,
            "allow_empty": allow_empty,
            "confidence_threshold": confidence_threshold,
        }
        if handoff_context:
            payload["handoff_context"] = handoff_context
        return self._client.call_tool(
            "propose_changeset",
            payload,
        )

    def record_run(
        self,
        *,
        model_slug: str,
        run_id: str,
        repo_path: str,
        instructions: str,
        blackboard: dict[str, Any],
        changeset_id: int | None,
        status: str,
        trigger: str,
        delta_summary: dict[str, Any],
        user: Any = None,
    ) -> dict[str, Any]:
        """Call MCP record_ratatosk_run."""
        logger.info(
            "McpHandoffPort.record_run | model=%s run_id=%s changeset_id=%s",
            model_slug,
            run_id,
            changeset_id,
        )
        return self._client.call_tool(
            "record_ratatosk_run",
            {
                "model": model_slug,
                "run_id": run_id,
                "repo_path": repo_path,
                "instructions": instructions,
                "blackboard": blackboard,
                "changeset_id": changeset_id,
                "status": status,
                "trigger": trigger,
                "delta_summary": delta_summary,
            },
        )
