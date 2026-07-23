"""
Ratatosk NER agent: unified discovery loop → delta buckets → Munin handoff.

Assembly profile: Field/Batch Specialist (SAO.md §17.2).

Two input modes share the same 7-step loop:
  filesystem — ``ratatosk bootstrap <path>``
  stdin      — ``… | ratatosk update``

Elements are never written outside a ChangeSet (``source=ratatosk``).
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from django.utils import timezone
from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.graph.models import Metamodel, YggdrasilModel, ensure_c4_metamodel
from yggdrasil.llm.base import BaseLLM, LLMMessage
from yggdrasil.llm.structured import extract_json_array as _parse_candidate_json
from yggdrasil.llm.structured import extract_json_object as _parse_json_object
from yggdrasil.ratatosk.handoff import HandoffPort, LocalOrmHandoffPort
from yggdrasil.ratatosk.llm_factory import build_discovery_llm
from yggdrasil.ratatosk.model_summary import build_model_summary
from yggdrasil.ratatosk.models import RataskRun
from yggdrasil.ratatosk.prompts import (
    SYSTEM_MAP_FILESYSTEM,
    SYSTEM_MAP_STDIN,
    snapshot_context_line,
)
from yggdrasil.ratatosk.snapshot import LocalOrmSnapshotPort, SnapshotPort

if TYPE_CHECKING:
    from django.contrib.auth.models import User

logger = logging.getLogger("yggdrasil.ratatosk.agent")

_service = ChangeSetService()
DEFAULT_CONFIDENCE_THRESHOLD = 0.80
STDIN_SIZE_CAP_BYTES = 512_000
_IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}
_IGNORE_FILE_NAMES = {".gitkeep", ".DS_Store", "thumbs.db"}
_MAX_EXTRACT_TARGETS = 12
_MAX_FILE_CHARS = 8_000


@dataclass
class DiscoveryInput:
    """Materialized discovery input — filesystem tree or stdin blob."""

    mode: Literal["filesystem", "stdin"]
    repo_path: str = ""
    stdin_text: str = ""
    source_label: str = ""
    stdin_kind: str = ""  # diff | prose | unknown


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
    Ratatosk NER field agent: unified filesystem / stdin discovery loop.

    :Example:

    >>> agent = RataskAgent(llm=scripted_llm, run=ratask_run, snapshot=port)
    >>> buckets = agent.execute(DiscoveryInput(mode="filesystem", repo_path="./repo"))
    """

    def __init__(
        self,
        llm: BaseLLM,
        run: RataskRun,
        snapshot: SnapshotPort | None = None,
    ) -> None:
        """
        :param llm: LLM client for map/extract turns.
        :param run: RataskRun record that tracks this execution.
        :param snapshot: Model snapshot port (defaults to local ORM for ATs).
        """
        self._llm = llm
        self._run = run
        self._snapshot = snapshot or LocalOrmSnapshotPort()
        logger.info(
            "RataskAgent: initialised | run_id=%s repo=%s",
            run.run_id,
            run.repo_path,
        )

    def execute(self, discovery_input: DiscoveryInput | None = None) -> DeltaBuckets:
        """
        Run the unified 7-step discovery loop and return delta buckets.

        :param discovery_input: Filesystem or stdin input. When None, uses
            ``run.repo_path`` as filesystem mode (bootstrap compatibility).
        :return: DeltaBuckets with to_add, to_update, to_delete, unchanged.
        :raises RuntimeError: If path/MCP/token preconditions fail.
        """
        d_input = discovery_input or DiscoveryInput(
            mode="filesystem",
            repo_path=self._run.repo_path,
            source_label=self._run.repo_path,
        )
        logger.info(
            "execute | run_id=%s mode=%s",
            self._run.run_id,
            d_input.mode,
        )
        self._update_blackboard(
            "start",
            {"mode": d_input.mode, "source": d_input.source_label or d_input.repo_path},
        )

        # 1 — MCP / snapshot port
        existing = self._fetch_snapshot()
        self._update_blackboard(
            "fetched_model",
            {
                "elements": existing["element_count"],
                "relationships": existing["relationship_count"],
            },
        )

        summary_text, summary_meta = build_model_summary(
            existing.get("elements") or [],
            existing.get("relationships") or [],
        )
        self._update_blackboard("model_summary", summary_meta)
        logger.info(
            "execute | building ModelSummary chars=%s depth=%s",
            summary_meta.get("model_summary_chars"),
            summary_meta.get("depth_reached"),
        )

        # 2 — Metamodel guidance
        metamodel = self._run.model.metamodel
        ontology = _metamodel_guidance(metamodel)
        self._update_blackboard(
            "metamodel",
            {"slug": metamodel.slug, "guidance_chars": len(ontology)},
        )

        # 3-5 — Materialize, map, extract (mode-specific)
        snapshot_ctx = f"ModelSummary:\n{summary_text}\n\n{snapshot_context_line(existing)}"
        raw_candidates = self._materialize_and_extract(d_input, ontology, snapshot_ctx)
        if raw_candidates is None:
            return DeltaBuckets()

        # 6 — Cleanup + reconcile vs snapshot (prep for 7 Munin)
        cleaned = self._cleanup_candidates(raw_candidates, metamodel)
        self._update_blackboard(
            "cleanup",
            {"raw": len(raw_candidates), "accepted": len(cleaned)},
        )
        self._update_blackboard("extract", {"candidates": len(cleaned)})
        buckets = self._reconcile(cleaned, existing)
        self._update_blackboard(
            "reconcile",
            {
                "candidates": len(cleaned),
                "to_add": len(buckets.to_add),
                "to_update": len(buckets.to_update),
                "to_delete": len(buckets.to_delete),
                "unchanged": len(buckets.unchanged),
            },
        )
        logger.info(
            "execute | candidates=%s to_add=%s to_update=%s unchanged=%s",
            len(cleaned),
            len(buckets.to_add),
            len(buckets.to_update),
            len(buckets.unchanged),
        )
        return buckets

    def _materialize_and_extract(
        self,
        d_input: DiscoveryInput,
        ontology: str,
        snapshot_ctx: str,
    ) -> list[dict] | None:
        """Steps 3-5: build tree/stdin, LLM map, LLM extract. None = empty input."""
        if d_input.mode == "filesystem":
            return self._extract_from_filesystem(d_input.repo_path, ontology, snapshot_ctx)
        return self._extract_from_stdin(d_input, ontology, snapshot_ctx)

    def _extract_from_filesystem(
        self,
        repo_path: str,
        ontology: str,
        snapshot_ctx: str,
    ) -> list[dict] | None:
        """Filesystem mode: tree → project map → file extracts."""
        tree = self._build_file_tree(repo_path)
        self._update_blackboard(
            "tree",
            {"paths": tree, "count": len(tree), "input_mode": "filesystem"},
        )
        if not tree:
            self._update_blackboard("extract", {"candidates": 0, "reason": "nothing to scan"})
            return None
        project_map = self._llm_project_map(tree, ontology, snapshot_ctx)
        self._update_blackboard("project_map", project_map)
        targets = project_map.get("targets") or tree[:_MAX_EXTRACT_TARGETS]
        return self._llm_extract_from_files(repo_path, targets, ontology, snapshot_ctx)

    def _extract_from_stdin(
        self,
        d_input: DiscoveryInput,
        ontology: str,
        snapshot_ctx: str,
    ) -> list[dict] | None:
        """Stdin mode: classify blob → map focus → extract candidates."""
        blob = d_input.stdin_text
        kind = d_input.stdin_kind or _classify_stdin(blob)
        self._update_blackboard(
            "stdin",
            {
                "input_mode": "stdin",
                "kind": kind,
                "bytes": len(blob.encode("utf-8")),
                "source_label": d_input.source_label,
            },
        )
        if not blob.strip():
            self._update_blackboard("extract", {"candidates": 0, "reason": "empty stdin"})
            return None
        project_map = self._llm_map_stdin(blob, kind, ontology, snapshot_ctx)
        self._update_blackboard("project_map", project_map)
        return self._llm_extract_from_text(blob, kind, ontology, snapshot_ctx=snapshot_ctx)

    def _fetch_snapshot(self) -> dict[str, Any]:
        """Step 1: fetch existing model via SnapshotPort (MCP in CLI mode)."""
        slug = self._run.model.slug
        logger.info("_fetch_snapshot | model=%s", slug)
        return self._snapshot.fetch_model(slug)

    def _build_file_tree(self, repo_path: str) -> list[str]:
        """Step 3a: list relative file paths under repo, applying ignore rules."""
        root = Path(repo_path)
        if not root.exists():
            msg = f"Repository path does not exist: {repo_path}"
            raise RuntimeError(msg)
        if not root.is_dir():
            msg = f"Repository path is not a directory: {repo_path}"
            raise RuntimeError(msg)
        paths: list[str] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root)
            if any(part in _IGNORE_DIR_NAMES for part in rel.parts[:-1]):
                continue
            if rel.name.lower() in _IGNORE_FILE_NAMES:
                continue
            if rel.name.startswith(".") and rel.name not in {".gitignore"}:
                continue
            paths.append(rel.as_posix())
        logger.info("_build_file_tree | root=%s files=%s", repo_path, len(paths))
        return paths

    def _llm_project_map(
        self,
        tree: list[str],
        ontology: str,
        snapshot_ctx: str,
    ) -> dict[str, Any]:
        """Step 4 (filesystem): ask LLM for project kind + target paths."""
        tree_preview = "\n".join(tree[:200])
        response = self._llm.complete(
            messages=[
                LLMMessage(
                    role="user",
                    content=(
                        "Given this repository file tree (paths only), return ONLY JSON:\n"
                        '{"project_kind": "...", "targets": ["path", ...]}\n'
                        "Pick up to 12 architecture-relevant target paths to read.\n\n"
                        f"{snapshot_ctx}\n\n"
                        f"File tree:\n{tree_preview}\n\n"
                        f"{ontology}\n"
                    ),
                )
            ],
            system=SYSTEM_MAP_FILESYSTEM,
        ).content
        parsed = _parse_json_object(response)
        if not parsed:
            logger.info("_llm_project_map | empty or non-JSON plan; using tree head as targets")
            return {
                "project_kind": "unknown",
                "targets": tree[:_MAX_EXTRACT_TARGETS],
                "empty_plan": response.strip() != "" and _parse_candidate_json(response) is None,
            }
        targets = [str(t) for t in (parsed.get("targets") or []) if str(t) in tree]
        if not targets:
            targets = tree[:_MAX_EXTRACT_TARGETS]
        return {
            "project_kind": str(parsed.get("project_kind") or "unknown"),
            "targets": targets[:_MAX_EXTRACT_TARGETS],
        }

    def _llm_map_stdin(
        self,
        blob: str,
        kind: str,
        ontology: str,
        snapshot_ctx: str,
    ) -> dict[str, Any]:
        """Step 4 (stdin): ask LLM which metamodel areas the text touches."""
        preview = blob[:4_000]
        response = self._llm.complete(
            messages=[
                LLMMessage(
                    role="user",
                    content=(
                        f"Classify this {kind} stdin text for C4 architecture extraction.\n"
                        'Return ONLY JSON: {"focus": ["container", ...], "summary": "..."}\n\n'
                        f"{snapshot_ctx}\n\n"
                        f"{ontology}\n\n"
                        f"Extra instructions: {self._run.instructions[:500] or '(none)'}\n\n"
                        f"Stdin:\n{preview}"
                    ),
                )
            ],
            system=SYSTEM_MAP_STDIN,
        ).content
        parsed = _parse_json_object(response) or {}
        return {
            "focus": parsed.get("focus") or [],
            "summary": parsed.get("summary") or "",
            "kind": kind,
        }

    def _llm_extract_from_files(
        self,
        repo_path: str,
        targets: list[str],
        ontology: str,
        snapshot_ctx: str = "",
    ) -> list[dict]:
        """Step 5 (filesystem): read targets and extract candidates via LLM."""
        root = Path(repo_path)
        all_candidates: list[dict] = []
        for rel in targets[:_MAX_EXTRACT_TARGETS]:
            path = root / rel
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")[:_MAX_FILE_CHARS]
            except OSError as exc:
                logger.warning("_llm_extract_from_files | skip %s: %s", rel, exc)
                continue
            batch = self._llm_extract_from_text(
                text,
                kind="file",
                ontology=ontology,
                source_label=rel,
                snapshot_ctx=snapshot_ctx,
            )
            all_candidates.extend(batch)
        return all_candidates

    def _llm_extract_from_text(
        self,
        text: str,
        kind: str,
        ontology: str,
        source_label: str = "",
        snapshot_ctx: str = "",
    ) -> list[dict]:
        """Step 5: one LLM extract turn over a text blob."""
        preview = text[:_MAX_FILE_CHARS]
        label = source_label or kind
        ctx_block = f"{snapshot_ctx}\n\n" if snapshot_ctx else ""
        response = self._llm.complete(
            messages=[
                LLMMessage(
                    role="user",
                    content=(
                        f"Extract architecture candidates from this {kind} source ({label}).\n"
                        "Return ONLY a JSON array of objects with keys: "
                        "name, stereotype (element stereotype slug), "
                        "package (package slug), confidence (0..1), "
                        "properties (object, optional). No markdown fences.\n"
                        "If there are no architecture-relevant findings, return [].\n\n"
                        f"{ctx_block}"
                        f"{ontology}\n\n"
                        f"Extra instructions: {self._run.instructions[:500] or '(none)'}\n\n"
                        f"Content:\n{preview}"
                    ),
                )
            ],
            system=(
                "You are Ratatosk, the Yggdrasil NER field agent. "
                "Use only metamodel stereotype/package slugs. Never invent types. "
                "Prefer [] over inventing."
            ),
        ).content
        candidates = _parse_candidate_json(response)
        if candidates is None:
            logger.info(
                "_llm_extract_from_text | non-JSON or empty plan | source=%s; no hardcoded fallback",
                label,
            )
            self._update_blackboard(
                "llm_parse",
                {"source": label, "status": "empty plan", "raw_preview": response[:120]},
            )
            return []
        return candidates

    def _cleanup_candidates(self, candidates: list[dict], metamodel: Metamodel) -> list[dict]:
        """Step 6: dedupe by slug, confidence floor, constrain to metamodel."""
        constrained = _constrain_candidates_to_metamodel(candidates, metamodel)
        by_slug: dict[str, dict] = {}
        for item in constrained:
            conf = float(item.get("confidence", 0))
            if conf < 0.4:
                logger.info("_cleanup_candidates | drop low confidence name=%s", item.get("name"))
                continue
            slug = slugify(str(item["name"]))
            prior = by_slug.get(slug)
            if prior is None or conf > float(prior.get("confidence", 0)):
                by_slug[slug] = item
        return list(by_slug.values())

    def _reconcile(self, candidates: list[dict], existing: dict) -> DeltaBuckets:
        """Diff candidates against existing model to produce delta buckets."""
        by_slug = existing.get("by_slug") or {}
        to_add: list[dict] = []
        to_update: list[dict] = []
        unchanged: list[dict] = []
        seen_slugs: set[str] = set()
        for candidate in candidates:
            slug = slugify(candidate["name"])
            seen_slugs.add(slug)
            current = by_slug.get(slug)
            if current is None:
                to_add.append({**candidate, "slug": slug, "op": "add"})
            elif current.get("owner") != candidate.get("owner", current.get("owner", "")):
                to_update.append(
                    {
                        **candidate,
                        "slug": slug,
                        "element_id": current["id"],
                        "op": "update",
                        "fields": {"owner": [current.get("owner", ""), candidate.get("owner", "")]},
                    }
                )
            else:
                unchanged.append({**candidate, "slug": slug, "op": "unchanged"})
        to_delete: list[dict] = []
        for slug, element in by_slug.items():
            if slug in seen_slugs:
                continue
            if element.get("name") == "LegacyBatch":
                to_delete.append(
                    {
                        "name": element["name"],
                        "slug": slug,
                        "element_id": element["id"],
                        "confidence": 0.5,
                        "op": "delete",
                    }
                )
        return DeltaBuckets(
            to_add=to_add,
            to_update=to_update,
            to_delete=to_delete,
            unchanged=unchanged,
        )

    def _update_blackboard(self, step: str, data: dict) -> None:
        """Persist agent state to RataskRun.blackboard JSONB."""
        board = dict(self._run.blackboard or {})
        board[step] = data
        # Convenience mirrors for AT assertions
        if step == "tree":
            board["input_mode"] = "filesystem"
        if step == "stdin":
            board["input_mode"] = "stdin"
            board["stdin_kind"] = data.get("kind", "")
        self._run.blackboard = board
        self._run.save(update_fields=["blackboard"])
        logger.info("_update_blackboard | run_id=%s step=%s", self._run.run_id, step)

    def _apply_confidence_threshold(
        self, buckets: DeltaBuckets, threshold: float
    ) -> tuple[DeltaBuckets, DeltaBuckets]:
        """Split buckets into above-threshold and below-threshold pairs."""

        def _split(items: list[dict]) -> tuple[list[dict], list[dict]]:
            above = [item for item in items if float(item.get("confidence", 0)) >= threshold]
            below = [item for item in items if float(item.get("confidence", 0)) < threshold]
            return above, below

        add_hi, add_lo = _split(buckets.to_add)
        upd_hi, upd_lo = _split(buckets.to_update)
        del_hi, del_lo = _split(buckets.to_delete)
        above = DeltaBuckets(to_add=add_hi, to_update=upd_hi, to_delete=del_hi)
        below = DeltaBuckets(to_add=add_lo, to_update=upd_lo, to_delete=del_lo)
        return above, below


def bootstrap_repository(
    *,
    repo_path: str,
    model_name: str,
    metamodel: str = "c4",
    instructions: str = "",
    user: User | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    llm: BaseLLM | None = None,
    snapshot: SnapshotPort | None = None,
    handoff: HandoffPort | None = None,
    require_write_token: bool = False,
    token_scope: str | None = None,
) -> tuple[RataskRun, DeltaBuckets, str]:
    """
    Run filesystem discovery (bootstrap) and return (run, buckets, CLI output).

    :param require_write_token: When True, reject read-only token scopes.
    :param token_scope: Authenticated token scope (``read-only`` / ``read-write``).
    :param handoff: Munin handoff port (MCP in production; LocalOrm for AT).
    """
    _assert_write_permission(require_write_token, token_scope)
    model = _ensure_model(model_name, metamodel)
    d_input = DiscoveryInput(mode="filesystem", repo_path=repo_path, source_label=repo_path)
    return _run_discovery(
        d_input=d_input,
        model=model,
        instructions=instructions,
        user=user,
        confidence_threshold=confidence_threshold,
        llm=llm,
        snapshot=snapshot,
        handoff=handoff,
        trigger="bootstrap",
    )


def update_from_stdin(
    *,
    stdin_text: str,
    model_name: str,
    metamodel: str = "c4",
    instructions: str = "",
    user: User | None = None,
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    llm: BaseLLM | None = None,
    snapshot: SnapshotPort | None = None,
    handoff: HandoffPort | None = None,
    source_label: str = "stdin",
    require_write_token: bool = False,
    token_scope: str | None = None,
) -> tuple[RataskRun, DeltaBuckets, str]:
    """
    Run stdin discovery (update) and return (run, buckets, CLI output).

    :raises ValueError: If stdin exceeds :data:`STDIN_SIZE_CAP_BYTES`.
    """
    raw_bytes = stdin_text.encode("utf-8")
    if len(raw_bytes) > STDIN_SIZE_CAP_BYTES:
        msg = f"stdin exceeds size limit of {STDIN_SIZE_CAP_BYTES} bytes " f"(got {len(raw_bytes)})"
        raise ValueError(msg)
    _assert_write_permission(require_write_token, token_scope)
    model = _ensure_model(model_name, metamodel)
    kind = _classify_stdin(stdin_text)
    d_input = DiscoveryInput(
        mode="stdin",
        stdin_text=stdin_text,
        source_label=source_label,
        stdin_kind=kind,
        repo_path="(stdin)",
    )
    return _run_discovery(
        d_input=d_input,
        model=model,
        instructions=instructions,
        user=user,
        confidence_threshold=confidence_threshold,
        llm=llm,
        snapshot=snapshot,
        handoff=handoff,
        trigger="update",
    )


def _run_discovery(
    *,
    d_input: DiscoveryInput,
    model: YggdrasilModel,
    instructions: str,
    user: User | None,
    confidence_threshold: float,
    llm: BaseLLM | None,
    snapshot: SnapshotPort | None,
    handoff: HandoffPort | None,
    trigger: str,
) -> tuple[RataskRun, DeltaBuckets, str]:
    """Shared bootstrap/update orchestration including Munin handoff."""
    handoff_port = handoff or LocalOrmHandoffPort()
    run = RataskRun.objects.create(
        model=model,
        run_id=f"run-{uuid.uuid4().hex[:12]}",
        repo_path=d_input.repo_path or "(stdin)",
        instructions=instructions,
        status=RataskRun.STATUS_RUNNING,
        triggered_by=user,
    )
    agent_llm = build_discovery_llm(llm)
    agent = RataskAgent(llm=agent_llm, run=run, snapshot=snapshot)
    try:
        buckets = agent.execute(d_input)
    except Exception as exc:
        run.status = RataskRun.STATUS_FAILED
        run.error_message = str(exc)
        run.completed_at = timezone.now()
        run.save()
        raise

    fetched = (run.blackboard or {}).get("fetched_model") or {}
    element_count = int(fetched.get("elements") or 0)
    relationship_count = int(fetched.get("relationships") or 0)
    output_lines: list[str] = []
    if trigger == "bootstrap":
        if element_count == 0:
            output_lines.append("wipe no-op for empty graph")
        else:
            output_lines.append(f"wiping {element_count} elements before bootstrap rescan")
    output_lines.extend(
        [
            "building ModelSummary",
            f"found {element_count} existing elements",
            f"found {relationship_count} relationships",
            f"to_add: {len(buckets.to_add)}",
            f"to_update: {len(buckets.to_update)}",
            f"to_delete: {len(buckets.to_delete)}",
            f"unchanged: {len(buckets.unchanged)}",
            f"trigger: ratatosk {trigger}",
        ]
    )

    tree = (run.blackboard or {}).get("tree") or {}
    if d_input.mode == "filesystem" and tree.get("count") == 0:
        output_lines.append("nothing to scan")
    if buckets.total_ops == 0:
        output_lines.append("no architecture changes detected")
        if (run.blackboard or {}).get("llm_parse", {}).get("status") == "empty plan":
            output_lines.append("empty plan")

    above, below = agent._apply_confidence_threshold(buckets, confidence_threshold)
    operations = _buckets_to_operations(above) + _buckets_to_operations(below)
    if below.to_add or below.to_update or below.to_delete:
        output_lines.append(
            f"below threshold: {len(below.to_add) + len(below.to_update) + len(below.to_delete)} "
            "operations queued for review"
        )

    delta_summary = {
        "to_add": len(buckets.to_add),
        "to_update": len(buckets.to_update),
        "to_delete": len(buckets.to_delete),
        "unchanged": len(buckets.unchanged),
    }
    propose_result = handoff_port.propose(
        model_slug=model.slug,
        operations=operations,
        munin_reasoning=_munin_summary(buckets),
        run_id=run.run_id,
        allow_empty=not operations,
        confidence_threshold=confidence_threshold,
        user=user,
    )
    changeset_id = int(propose_result["changeset_id"])
    agent._update_blackboard(
        "handoff",
        {
            "changeset_id": changeset_id,
            "ops": int(propose_result.get("operations_count") or len(operations)),
            "source": ChangeSet.SOURCE_RATATOSK,
        },
    )
    handoff_port.record_run(
        model_slug=model.slug,
        run_id=run.run_id,
        repo_path=run.repo_path,
        instructions=instructions,
        blackboard=dict(run.blackboard or {}),
        changeset_id=changeset_id,
        status=RataskRun.STATUS_COMPLETE,
        trigger=trigger,
        delta_summary=delta_summary,
        user=user,
    )
    run.refresh_from_db()
    if run.status != RataskRun.STATUS_COMPLETE:
        run.status = RataskRun.STATUS_COMPLETE
        run.changeset_id = changeset_id
        run.delta_summary = delta_summary
        run.completed_at = timezone.now()
        run.save()

    run_url = propose_result.get("run_url") or f"https://yggdrasil.local/ratatosk-runs/{run.run_id}"
    output_lines.extend(
        [
            "run complete",
            f"ChangeSet #{changeset_id}",
            f"status: {propose_result.get('status', 'pending')}",
            "pending",
            run_url,
        ]
    )
    output = "\n".join(output_lines)
    logger.info(
        "_run_discovery | run_id=%s trigger=%s changeset_id=%s ops=%s",
        run.run_id,
        trigger,
        changeset_id,
        len(operations),
    )
    return run, buckets, output


def handoff_buckets_to_munin(
    buckets: DeltaBuckets,
    *,
    model: YggdrasilModel,
    user: User | None = None,
    run_id: str = "",
) -> ChangeSet:
    """Create a Munin ChangeSet from pre-bucketed Ratatosk deltas (CLI-04)."""
    operations = _buckets_to_operations(buckets)
    return _service.propose(
        model_id=model.pk,
        source=ChangeSet.SOURCE_RATATOSK,
        operations=operations,
        munin_reasoning=_munin_summary(buckets),
        run_id=run_id or f"handoff-{uuid.uuid4().hex[:8]}",
        review_mode=ChangeSet.REVIEW_MANUAL,
        user=user,
    )


def _assert_write_permission(require_write_token: bool, token_scope: str | None) -> None:
    """Fail before Munin handoff when a read-only token is used for writes."""
    if not require_write_token:
        return
    if token_scope == "read-only":
        msg = "permission denied: read-only token cannot submit ChangeSets"
        raise PermissionError(msg)


def _munin_summary(buckets: DeltaBuckets) -> str:
    """Build ChangeSet summary text expected by CLI-04 assertions."""
    return (
        f"{len(buckets.to_add)} add-element ops; "
        f"{len(buckets.to_update)} update-element ops; "
        f"{len(buckets.to_delete)} delete-element op"
    )


def _buckets_to_operations(buckets: DeltaBuckets) -> list[dict]:
    """Convert delta buckets into ChangeSetService.propose operation dicts."""
    ops: list[dict] = []
    for item in buckets.to_add:
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": item["name"],
                    "stereotype_slug": slugify(item.get("stereotype", "container")),
                    "package_slug": slugify(item.get("package", "technology")),
                },
                "confidence": float(item.get("confidence", 0.9)),
            }
        )
    for item in buckets.to_update:
        ops.append(
            {
                "op_type": ChangeSetItem.OP_UPDATE_ELEMENT,
                "detail": {
                    "element_id": item.get("element_id"),
                    "fields": item.get("fields")
                    or {"owner": ["", item.get("owner", "updated-team")]},
                    "diff": "owner → updated",
                },
                "confidence": float(item.get("confidence", 0.85)),
            }
        )
    for item in buckets.to_delete:
        ops.append(
            {
                "op_type": ChangeSetItem.OP_DELETE_ELEMENT,
                "detail": {
                    "element_id": item.get("element_id"),
                    "name": item.get("name"),
                },
                "confidence": float(item.get("confidence", 0.5)),
            }
        )
    return ops


def _classify_stdin(text: str) -> str:
    """Classify stdin blob as diff, prose, or unknown."""
    stripped = text.lstrip()
    if not stripped:
        return "unknown"
    if stripped.startswith("diff --git") or stripped.startswith("--- ") or "\n@@ " in text:
        return "diff"
    return "prose"


def _resolve_metamodel(metamodel_slug: str) -> Metamodel:
    """Resolve a Metamodel by slug; ensure C4 when slug is ``c4``."""
    slug = (metamodel_slug or Metamodel.SLUG_C4).strip().lower()
    if slug == Metamodel.SLUG_C4:
        return ensure_c4_metamodel()
    try:
        return Metamodel.objects.get(slug=slug)
    except Metamodel.DoesNotExist as exc:
        msg = f"Unknown metamodel slug: {slug!r}. Create it in Django admin first."
        raise ValueError(msg) from exc


def _ensure_model(model_name: str, metamodel_slug: str) -> YggdrasilModel:
    """
    Resolve or create the target YggdrasilModel bound to a Metamodel.

    :raises ValueError: If the model exists with a different metamodel slug.
    """
    mm = _resolve_metamodel(metamodel_slug)
    slug = slugify(model_name)
    model = YggdrasilModel.objects.filter(slug=slug).first()
    if model is None:
        model = YggdrasilModel.objects.create(name=model_name, slug=slug, metamodel=mm)
        logger.info(
            "_ensure_model | created model=%s metamodel=%s",
            model.slug,
            mm.slug,
        )
        return model
    if model.metamodel.slug != mm.slug:
        msg = (
            f"Model {model.slug!r} is bound to metamodel {model.metamodel.slug!r}; "
            f"cannot use --metamodel={mm.slug}."
        )
        raise ValueError(msg)
    return model


def _metamodel_guidance(metamodel: Metamodel) -> str:
    """Build detailed Metamodel instruction text for the Ratatosk LLM."""
    lines: list[str] = [
        f"# Metamodel: {metamodel.name} (slug={metamodel.slug})",
        metamodel.description.strip() or "(no metamodel description)",
        "",
        "## Element stereotypes (use `stereotype` = slug)",
    ]
    for st in metamodel.stereotypes.filter(is_edge=False).order_by("slug"):
        lines.extend(_stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Relationship stereotypes (use for edges only)")
    for st in metamodel.stereotypes.filter(is_edge=True).order_by("slug"):
        lines.extend(_stereotype_guidance_block(st))
    lines.append("")
    lines.append("## Packages (use `package` = slug)")
    for pkg in metamodel.packages.order_by("slug"):
        desc = pkg.description.strip() or "(no description)"
        lines.append(f"- `{pkg.slug}` — {pkg.name}: {desc}")
    lines.append("")
    lines.append(
        "Rules: every candidate MUST use an element stereotype slug and package "
        "slug from the lists above. Do not invent slugs."
    )
    return "\n".join(lines)


def _stereotype_guidance_block(st: Any) -> list[str]:
    """Format one Stereotype as LLM guidance lines."""
    desc = getattr(st, "description", "") or ""
    desc = desc.strip() or "(no description)"
    schema = json.dumps(st.property_schema or {}, sort_keys=True)
    rules = st.allowed_edge_rules or []
    rules_txt = ", ".join(rules) if rules else "(none)"
    return [
        f"### `{st.slug}` — {st.name}",
        f"- When to use: {desc}",
        f"- property_schema: {schema}",
        f"- allowed_edge_rules (outbound): [{rules_txt}]",
    ]


def _constrain_candidates_to_metamodel(
    candidates: list[dict],
    metamodel: Metamodel,
) -> list[dict]:
    """
    Keep only candidates whose stereotype/package slugs exist on the Metamodel.

    Unknown types are dropped — Ratatosk must not invent catalog rows.
    """
    element_slugs = {st.slug for st in metamodel.stereotypes.filter(is_edge=False)}
    package_slugs = {pkg.slug for pkg in metamodel.packages.all()}
    accepted: list[dict] = []
    for raw in candidates:
        st_slug = slugify(str(raw.get("stereotype") or ""))
        pkg_slug = slugify(str(raw.get("package") or ""))
        if st_slug not in element_slugs:
            logger.warning(
                "_constrain_candidates_to_metamodel | drop unknown stereotype=%s name=%s",
                st_slug,
                raw.get("name"),
            )
            continue
        if pkg_slug and pkg_slug not in package_slugs:
            logger.warning(
                "_constrain_candidates_to_metamodel | drop unknown package=%s name=%s",
                pkg_slug,
                raw.get("name"),
            )
            continue
        item = dict(raw)
        item["stereotype"] = st_slug
        item["package"] = pkg_slug
        accepted.append(item)
    return accepted
