"""
Django-free discovery orchestration for the Ratatosk CLI.

Uses MCP client for snapshot, stereotypes, ensure_model, propose, record_run.
Never imports Django.
"""

from __future__ import annotations

import hashlib
import logging
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ratatosk.discovery.candidates import attach_source_paths, merge_candidates_by_slug
from ratatosk.discovery.exclude import normalize_exclude_patterns, path_is_excluded
from ratatosk.discovery.limits import (
    DiscoveryLimits,
    README_SOURCE,
    SAO_ARCHITECTURE_SOURCE,
    cap_extract_targets,
    prioritize_targets,
)
from ratatosk.discovery.model_summary import build_model_summary
from ratatosk.discovery.prefilter import prefilter_candidates
from ratatosk.discovery.synthesize import run_synthesis_phase
from yggdrasil.graph.metamodel_guidance import build_metamodel_guidance_from_stereotypes
from yggdrasil.llm.structured import extract_json_array as _parse_candidate_json
from yggdrasil.llm.structured import extract_json_object as _parse_json_object

logger = logging.getLogger("ratatosk.discovery.runner")

_PREVIEW_CHARS = 1200
_MAX_FILE_CHARS = 8_000
STDIN_SIZE_CAP_BYTES = 512_000
DEFAULT_CONFIDENCE_THRESHOLD = 0.80
_IGNORE_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}
_IGNORE_FILE_NAMES = {".gitkeep", ".DS_Store"}
_STEREOTYPE_DEFAULT_PACKAGE: dict[str, str] = {
    "container": "technology",
    "system": "technology",
    "component": "application",
    "person": "context",
}
_README_SOURCE = README_SOURCE


@dataclass
class DeltaBuckets:
    """Pre-bucketed NER deltas."""

    to_add: list[dict] = field(default_factory=list)
    to_update: list[dict] = field(default_factory=list)
    to_delete: list[dict] = field(default_factory=list)
    unchanged: list[dict] = field(default_factory=list)

    @property
    def total_ops(self) -> int:
        return len(self.to_add) + len(self.to_update) + len(self.to_delete)


def run_cli_discovery(
    *,
    client: Any,
    llm: Any,
    mode: Literal["filesystem", "stdin"],
    model_name: str,
    metamodel: str = "c4",
    instructions: str = "",
    repo_path: str = "",
    stdin_text: str = "",
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    exclude_patterns: list[str] | None = None,
    extract_llm: Any | None = None,
    planning_llm: Any | None = None,
    discovery_limits: DiscoveryLimits | None = None,
) -> tuple[str, DeltaBuckets, str]:
    """
    Run discovery and hand off via MCP. No Django.

    :param client: Object with ``call_tool(name, arguments) -> dict``.
    :param llm: Field-tier LLM (legacy param; use ``extract_llm`` when set).
    :param extract_llm: Haiku/fast model for per-file extract steps.
    :param planning_llm: Sonnet/planning model for ``_llm_project_map``.
    :param discovery_limits: Scout bounds (default 50 targets / 1000 file reads).
    :return: (run_id, buckets, CLI output text)
    """
    limits = discovery_limits or DiscoveryLimits()
    field_llm = extract_llm or llm
    map_llm = planning_llm or field_llm
    logger.info(
        "run_cli_discovery | entry mode=%s model=%s metamodel=%s confidence_threshold=%s "
        "max_extract_targets=%s max_file_reads=%s planning_llm=%s extract_llm=%s",
        mode,
        model_name,
        metamodel,
        confidence_threshold,
        limits.max_extract_targets,
        limits.max_file_reads_per_run,
        getattr(map_llm, "model_id", type(map_llm).__name__),
        getattr(field_llm, "model_id", type(field_llm).__name__),
    )
    if mode == "filesystem":
        logger.info(
            "run_cli_discovery | validation repo_path=%s exists=%s",
            repo_path,
            bool(repo_path and Path(repo_path).exists()),
        )
    else:
        stdin_bytes = len(stdin_text.encode("utf-8"))
        logger.info(
            "run_cli_discovery | validation stdin_bytes=%s cap=%s within_cap=%s",
            stdin_bytes,
            STDIN_SIZE_CAP_BYTES,
            stdin_bytes <= STDIN_SIZE_CAP_BYTES,
        )
    ensured = client.call_tool("ensure_model", {"model": model_name, "metamodel": metamodel})
    model_slug = str(ensured["slug"])
    logger.info(
        "run_cli_discovery | ensure_model model_slug=%s metamodel=%s created=%s",
        model_slug,
        ensured.get("metamodel"),
        ensured.get("created"),
    )

    logger.info("run_cli_discovery | fetching existing model state via MCP")
    elements_page = client.call_tool(
        "list_elements", {"model": model_slug, "limit": 200, "offset": 0}
    )
    rel_page = client.call_tool("list_relationships", {"model": model_slug, "limit": 200})
    elements = list(elements_page.get("items") or [])
    relationships = list(rel_page.get("items") or [])
    element_count = int(elements_page.get("total") or len(elements))
    relationship_count = int(rel_page.get("total") or len(relationships))
    by_slug = {
        _slugify(str(item.get("slug") or item.get("name") or "")): item
        for item in elements
        if item.get("name") or item.get("slug")
    }

    summary_text, summary_meta = build_model_summary(elements, relationships)
    logger.info(
        "run_cli_discovery | building ModelSummary chars=%s depth=%s",
        summary_meta.get("model_summary_chars"),
        summary_meta.get("depth_reached"),
    )

    stereotypes = client.call_tool("list_stereotypes", {"model": model_slug})
    stereotype_items = stereotypes.get("items") or []
    ontology, element_slugs, package_slugs = _guidance_from_stereotypes(stereotype_items)
    logger.info(
        "run_cli_discovery | metamodel_guidance stereotype_items=%s element_slugs=%s "
        "package_slugs=%s ontology_chars=%s instructions_chars=%s",
        len(stereotype_items),
        sorted(element_slugs),
        sorted(package_slugs),
        len(ontology),
        len(instructions),
    )

    exclude_patterns = normalize_exclude_patterns(exclude_patterns or [])
    instructions_preview = instructions[:80] if instructions else ""
    instructions_hash = (
        hashlib.sha256(instructions.encode("utf-8")).hexdigest()[:12] if instructions else ""
    )

    blackboard: dict[str, Any] = {
        "fetched_model": {
            "elements": element_count,
            "relationships": relationship_count,
        },
        "model_summary": summary_meta,
        "metamodel": {"slug": metamodel},
        "exclude_patterns": exclude_patterns,
        "instructions": {
            "chars": len(instructions),
            "preview": instructions_preview,
            "hash": instructions_hash,
        },
        "discovery_limits": {
            "max_extract_targets": limits.max_extract_targets,
            "max_file_reads_per_run": limits.max_file_reads_per_run,
            "effective_cap": limits.effective_cap,
        },
        "llm_tiers": {
            "planning_model": getattr(map_llm, "model_id", type(map_llm).__name__),
            "extract_model": getattr(field_llm, "model_id", type(field_llm).__name__),
        },
    }

    if mode == "filesystem":
        logger.info(
            "run_cli_discovery | scan_start repo_path=%s reason=bootstrap_filesystem_scan",
            repo_path,
        )
        tree, skipped_exclude = _build_file_tree(repo_path, exclude_patterns)
        blackboard["tree"] = {"paths": tree, "count": len(tree)}
        blackboard["skipped_by_exclude_count"] = skipped_exclude
        blackboard["input_mode"] = "filesystem"
        if not tree:
            candidates: list[dict] = []
            blackboard["extract"] = {"candidates": 0, "reason": "nothing to scan"}
            logger.warning(
                "run_cli_discovery | scan_complete file_count=0 branch=nothing_to_scan "
                "reason=empty_tree",
            )
        else:
            project_map = _llm_project_map(map_llm, tree, ontology, limits, instructions)
            blackboard["project_map"] = project_map
            raw_targets = project_map.get("targets") or tree[: limits.effective_cap]
            targets = prioritize_targets(tree, raw_targets, limits)
            blackboard["llm_tiers"]["targets_planned"] = len(project_map.get("targets") or [])
            blackboard["llm_tiers"]["targets_extracted"] = len(targets)
            logger.info(
                "run_cli_discovery | scan_map_complete project_kind=%s "
                "tree_paths=%s mapped_targets=%s targets=%s effective_cap=%s",
                project_map.get("project_kind"),
                len(tree),
                len(project_map.get("targets") or []),
                targets,
                limits.effective_cap,
            )
            candidates = _llm_extract_files(
                field_llm, repo_path, targets, ontology, instructions, limits
            )
            logger.info(
                "run_cli_discovery | extract_complete raw_candidates=%s summary=%s",
                len(candidates),
                _summarize_candidates(candidates),
            )
    else:
        kind = _classify_stdin(stdin_text)
        blackboard["stdin"] = {"kind": kind, "bytes": len(stdin_text.encode("utf-8"))}
        blackboard["input_mode"] = "stdin"
        blackboard["stdin_kind"] = kind
        if not stdin_text.strip():
            candidates = []
            blackboard["extract"] = {"candidates": 0, "reason": "empty stdin"}
        else:
            _llm_map_stdin(map_llm, stdin_text, kind, ontology, instructions)
            candidates = _llm_extract_text(
                field_llm, stdin_text, kind, ontology, instructions, source_label="stdin"
            )
            candidates = merge_candidates_by_slug(candidates)

    synthesis_meta: dict[str, Any] = {}
    if candidates:
        pf = prefilter_candidates(candidates)
        blackboard["prefilter"] = {
            "input": len(candidates),
            "kept": len(pf.kept),
            "rejected": len(pf.rejected),
        }
        candidates, synthesis_meta = run_synthesis_phase(
            map_llm,
            pf.kept,
            ontology,
            pf.cluster_hints,
            instructions,
        )
        blackboard["synthesize"] = synthesis_meta
        logger.info(
            "run_cli_discovery | synthesize before=%s after=%s merges=%s fallback=%s",
            synthesis_meta.get("before_count"),
            synthesis_meta.get("after_count"),
            len(synthesis_meta.get("merges") or []),
            synthesis_meta.get("fallback"),
        )
    else:
        blackboard["prefilter"] = {"input": 0, "kept": 0, "rejected": 0}
        blackboard["synthesize"] = {
            "canonical_count": 0,
            "merges": [],
            "rejects": [],
            "do_not_reference": [],
        }

    cleaned = _cleanup(candidates, element_slugs, package_slugs)
    blackboard["cleanup"] = {"raw": len(candidates), "accepted": len(cleaned)}
    blackboard["extract"] = {"candidates": len(cleaned)}
    logger.info(
        "run_cli_discovery | cleanup raw=%s accepted=%s dropped=%s " "before=%s after=%s",
        len(candidates),
        len(cleaned),
        len(candidates) - len(cleaned),
        _summarize_candidates(candidates),
        _summarize_candidates(cleaned),
    )
    buckets = _reconcile(cleaned, by_slug, bootstrap_rescan=(mode == "filesystem"))
    logger.info(
        "run_cli_discovery | reconcile to_add=%s to_update=%s to_delete=%s unchanged=%s "
        "add_names=%s",
        len(buckets.to_add),
        len(buckets.to_update),
        len(buckets.to_delete),
        len(buckets.unchanged),
        [item.get("name") for item in buckets.to_add],
    )

    wipe_line = ""
    if mode == "filesystem":
        if buckets.to_delete:
            wipe_line = (
                f"wiping {len(buckets.to_delete)} elements and "
                f"{relationship_count} relationships before bootstrap rescan"
            )
        elif element_count == 0:
            wipe_line = "wipe no-op for empty graph"
        if wipe_line:
            logger.info("run_cli_discovery | %s", wipe_line)

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    operations = _buckets_to_operations(buckets, confidence_threshold)
    # Include below-threshold ops too (server splits apply)
    operations = _all_bucket_operations(buckets, bootstrap_rescan=(mode == "filesystem"))
    logger.info(
        "run_cli_discovery | munin_handoff_start run_id=%s ratatosk_element_ops=%s "
        "confidence_threshold=%s op_types=%s",
        run_id,
        len(operations),
        confidence_threshold,
        _summarize_op_types(operations),
    )

    propose = client.call_tool(
        "propose_changeset",
        {
            "model": model_slug,
            "operations": operations,
            "source": "ratatosk",
            "munin_reasoning": (
                f"{len(buckets.to_add)} add-element ops; "
                f"{len(buckets.to_update)} update-element ops; "
                f"{len(buckets.to_delete)} delete-element op"
            ),
            "run_id": run_id,
            "allow_empty": not operations,
            "confidence_threshold": confidence_threshold,
            "handoff_context": {
                "synthesize": {
                    "merges": synthesis_meta.get("merges") or [],
                    "rejects": synthesis_meta.get("rejects") or [],
                    "do_not_reference": synthesis_meta.get("do_not_reference") or [],
                    "canonical_count": synthesis_meta.get("canonical_count", len(cleaned)),
                },
                "instructions": instructions,
                "metamodel_slug": metamodel,
            },
        },
    )
    changeset_id = propose["changeset_id"]
    munin_reasoning = str(propose.get("munin_reasoning") or "")
    if "0 add-relationship ops" in munin_reasoning and "source=none" in munin_reasoning:
        warning = (
            "WARNING: Munin bootstrap produced zero relationships — "
            "graph will have no edges until relationships are planned"
        )
        logger.warning("run_cli_discovery | %s | munin_reasoning=%s", warning, munin_reasoning)
        print(warning, file=sys.stderr)
    blackboard["handoff"] = {
        "changeset_id": changeset_id,
        "ops": propose.get("operations_count", len(operations)),
        "source": "ratatosk",
    }
    logger.info(
        "run_cli_discovery | munin_handoff_complete changeset_id=%s "
        "ratatosk_ops=%s total_ops=%s applied=%s pending=%s status=%s",
        changeset_id,
        len(operations),
        propose.get("operations_count", len(operations)),
        propose.get("applied_count", 0),
        propose.get("pending_count", 0),
        propose.get("status", "pending"),
    )
    client.call_tool(
        "record_ratatosk_run",
        {
            "model": model_slug,
            "run_id": run_id,
            "repo_path": repo_path if mode == "filesystem" else "(stdin)",
            "instructions": instructions,
            "blackboard": blackboard,
            "changeset_id": changeset_id,
            "status": "complete",
            "trigger": "bootstrap" if mode == "filesystem" else "update",
            "delta_summary": {
                "to_add": len(buckets.to_add),
                "to_update": len(buckets.to_update),
                "to_delete": len(buckets.to_delete),
                "unchanged": len(buckets.unchanged),
            },
        },
    )

    output_lines: list[str] = []
    if wipe_line:
        output_lines.append(wipe_line)
    if mode == "filesystem" and instructions.strip():
        output_lines.append(f"scanning {repo_path} with instructions")
    output_lines.extend(
        _format_discovery_output_lines(
            element_count=element_count,
            relationship_count=relationship_count,
            buckets=buckets,
            trigger="bootstrap" if mode == "filesystem" else "update",
            bootstrap_rescan=(mode == "filesystem"),
        )
    )
    if mode == "filesystem" and blackboard.get("tree", {}).get("count") == 0:
        output_lines.append("nothing to scan")
    if buckets.total_ops == 0:
        output_lines.append("no architecture changes detected")
    pending = int(propose.get("pending_count") or 0)
    if pending:
        output_lines.append(f"below threshold: {pending} operations queued for review")
    run_url = propose.get("run_url") or f"https://yggdrasil.local/ratatosk-runs/{run_id}"
    output_lines.extend(
        [
            "run complete",
            f"ChangeSet #{changeset_id}",
            f"status: {propose.get('status', 'pending')}",
            "pending",
            run_url,
        ]
    )
    output = "\n".join(output_lines)
    logger.info(
        "run_cli_discovery | run_id=%s changeset_id=%s ops=%s",
        run_id,
        changeset_id,
        len(operations),
    )
    return run_id, buckets, output


def _build_file_tree(
    repo_path: str,
    exclude_patterns: list[str] | None = None,
) -> tuple[list[str], int]:
    """Walk repo_path and return relative file paths (ignored dirs skipped)."""
    patterns = exclude_patterns or []
    logger.info(
        "_build_file_tree | entry repo_path=%s ignore_dirs=%s ignore_files=%s exclude=%s",
        repo_path,
        sorted(_IGNORE_DIR_NAMES),
        sorted(_IGNORE_FILE_NAMES),
        patterns,
    )
    root = Path(repo_path)
    if not root.exists():
        raise RuntimeError(f"Repository path does not exist: {repo_path}")
    if not root.is_dir():
        raise RuntimeError(f"Repository path is not a directory: {repo_path}")
    paths: list[str] = []
    skipped_dirs = 0
    skipped_files = 0
    skipped_exclude = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_posix = rel.as_posix()
        if any(part in _IGNORE_DIR_NAMES for part in rel.parts[:-1]):
            skipped_dirs += 1
            continue
        if rel.name.lower() in _IGNORE_FILE_NAMES:
            skipped_files += 1
            continue
        if path_is_excluded(rel_posix, patterns):
            skipped_exclude += 1
            logger.info(
                "_build_file_tree | excluded path=%s reason=exclude_pattern",
                rel_posix,
            )
            continue
        paths.append(rel_posix)
    preview = paths[:8]
    tail = paths[-3:] if len(paths) > 8 else []
    logger.info(
        "_build_file_tree | result file_count=%s skipped_under_ignore_dir=%s "
        "skipped_ignore_file=%s skipped_exclude=%s head=%s tail=%s",
        len(paths),
        skipped_dirs,
        skipped_files,
        skipped_exclude,
        preview,
        tail,
    )
    return paths, skipped_exclude


def _classify_stdin(text: str) -> str:
    stripped = text.lstrip()
    if not stripped:
        return "unknown"
    if stripped.startswith("diff --git") or stripped.startswith("--- ") or "\n@@ " in text:
        return "diff"
    return "prose"


def _guidance_from_stereotypes(
    items: list[dict],
) -> tuple[str, set[str], set[str]]:
    element_slugs = {
        str(st.get("slug") or "") for st in items if not st.get("is_edge") and st.get("slug")
    }
    package_slugs = {"context", "technology", "application", "code"}
    ontology = build_metamodel_guidance_from_stereotypes(items, metamodel_slug="c4")
    return ontology, element_slugs, package_slugs


def _llm_project_map(
    llm: Any,
    tree: list[str],
    ontology: str,
    limits: DiscoveryLimits,
    instructions: str = "",
) -> dict[str, Any]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    max_targets = limits.max_extract_targets
    logger.info(
        "_llm_project_map | entry tree_paths=%s ontology_chars=%s llm=%s max_targets=%s",
        len(tree),
        len(ontology),
        getattr(llm, "model_id", type(llm).__name__),
        max_targets,
    )
    tree_preview = "\n".join(tree[:200])
    system = (
        "You are Ratatosk planning bootstrap discovery. Return JSON only. "
        "Pick architecture-relevant paths diligently through the full tree — "
        "not alphabetical head, not only top-level files."
    )
    instructions_block = instructions[:500] or "(none)"
    user_content = (
        "Given this repository file tree (paths only), return ONLY JSON:\n"
        '{"project_kind": "...", "targets": ["path", ...]}\n'
        f"Select up to {max_targets} paths worth reading for C4 architecture extraction.\n"
        f"Always include {README_SOURCE} and {SAO_ARCHITECTURE_SOURCE} when present.\n"
        "Prefer: architecture docs, README, docker-compose, package manifests, "
        "service entrypoints, Django apps, MCP/server modules — over __init__.py noise.\n"
        f"Instructions: {instructions_block}\n\n"
        f"File tree ({len(tree)} paths):\n{tree_preview}\n\n{ontology}\n"
    )
    logger.info(
        "_llm_project_map | request system_chars=%s user_chars=%s preview=%s",
        len(system),
        len(user_content),
        _preview(user_content),
    )
    response = llm.complete(
        messages=[LLMMessage(role="user", content=user_content)],
        system=system,
    ).content
    logger.info(
        "_llm_project_map | response chars=%s preview=%s",
        len(response),
        _preview(response),
    )
    parsed = _parse_json_object(response) or {}
    tree_set = set(tree)
    targets = [str(t) for t in (parsed.get("targets") or []) if str(t) in tree_set]
    dropped_unknown = len(parsed.get("targets") or []) - len(targets)
    if dropped_unknown:
        logger.info(
            "_llm_project_map | dropped_unknown_paths=%s reason=not_in_tree",
            dropped_unknown,
        )
    if README_SOURCE in tree and README_SOURCE not in targets:
        targets.insert(0, README_SOURCE)
    if SAO_ARCHITECTURE_SOURCE in tree and SAO_ARCHITECTURE_SOURCE not in targets:
        insert_at = 1 if targets and targets[0] == README_SOURCE else 0
        targets.insert(insert_at, SAO_ARCHITECTURE_SOURCE)
    if not targets:
        targets = tree[: limits.effective_cap]
        logger.info(
            "_llm_project_map | branch=fallback_tree_head targets=%s reason=empty_or_invalid_json",
            len(targets),
        )
    else:
        logger.info(
            "_llm_project_map | branch=llm_targets count=%s project_kind=%s",
            len(targets),
            parsed.get("project_kind"),
        )
    return {
        "project_kind": str(parsed.get("project_kind") or "unknown"),
        "targets": cap_extract_targets(targets, limits),
    }


def _llm_map_stdin(
    llm: Any, blob: str, kind: str, ontology: str, instructions: str
) -> dict[str, Any]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    logger.info(
        "_llm_map_stdin | entry kind=%s blob_chars=%s instructions_chars=%s llm=%s",
        kind,
        len(blob),
        len(instructions),
        getattr(llm, "model_id", type(llm).__name__),
    )
    system = "You are Ratatosk mapping stdin. JSON only."
    user_content = (
        f"Classify this {kind} stdin for architecture extraction.\n"
        f"{ontology}\nInstructions: {instructions[:500] or '(none)'}\n"
        f"Stdin:\n{blob[:4000]}"
    )
    logger.info(
        "_llm_map_stdin | request system_chars=%s user_chars=%s preview=%s",
        len(system),
        len(user_content),
        _preview(user_content),
    )
    response = llm.complete(
        messages=[LLMMessage(role="user", content=user_content)],
        system=system,
    ).content
    logger.info(
        "_llm_map_stdin | response chars=%s preview=%s",
        len(response),
        _preview(response),
    )
    parsed = _parse_json_object(response) or {}
    logger.info(
        "_llm_map_stdin | kind=%s focus=%s summary_chars=%s",
        kind,
        parsed.get("focus"),
        len(str(parsed.get("summary") or "")),
    )
    return parsed


def _llm_extract_files(
    llm: Any,
    repo_path: str,
    targets: list[str],
    ontology: str,
    instructions: str,
    limits: DiscoveryLimits | None = None,
) -> list[dict]:
    """Read each target file from disk and run LLM extract (paths-only map precedes this)."""
    effective = limits or DiscoveryLimits()
    bounded = targets[: effective.max_file_reads_per_run]
    logger.info(
        "_llm_extract_files | entry repo_path=%s target_count=%s max_file_reads=%s "
        "extract_llm=%s targets=%s",
        repo_path,
        len(bounded),
        effective.max_file_reads_per_run,
        getattr(llm, "model_id", type(llm).__name__),
        bounded,
    )
    root = Path(repo_path)
    all_c: list[dict] = []
    read_count = 0
    skipped_missing = 0
    for index, rel in enumerate(bounded, start=1):
        path = root / rel
        if not path.is_file():
            skipped_missing += 1
            logger.warning(
                "_llm_extract_files | skip path=%s reason=not_a_file_or_missing",
                rel,
            )
            continue
        raw_bytes = path.stat().st_size
        text = path.read_text(encoding="utf-8", errors="replace")[:_MAX_FILE_CHARS]
        read_count += 1
        logger.info(
            "_llm_extract_files | read index=%s path=%s bytes=%s extracted_chars=%s capped=%s",
            index,
            rel,
            raw_bytes,
            len(text),
            raw_bytes > _MAX_FILE_CHARS or len(text) >= _MAX_FILE_CHARS,
        )
        file_candidates = _llm_extract_text(
            llm, text, "file", ontology, instructions, source_label=rel
        )
        all_c.extend(file_candidates)
        logger.info(
            "_llm_extract_files | file_done path=%s file_candidates=%s running_total=%s",
            rel,
            len(file_candidates),
            len(all_c),
        )
    logger.info(
        "_llm_extract_files | result files_read=%s skipped_missing=%s raw_candidates=%s summary=%s",
        read_count,
        skipped_missing,
        len(all_c),
        _summarize_candidates(all_c),
    )
    return merge_candidates_by_slug(all_c)


def _llm_extract_text(
    llm: Any,
    text: str,
    kind: str,
    ontology: str,
    instructions: str,
    source_label: str,
) -> list[dict]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    logger.info(
        "_llm_extract_text | entry source=%s kind=%s text_chars=%s llm=%s",
        source_label,
        kind,
        len(text),
        getattr(llm, "model_id", type(llm).__name__),
    )
    system = "You are Ratatosk. Use only listed stereotype slugs. Prefer [] over inventing."
    if source_label.endswith(_README_SOURCE):
        user_content = (
            f"Extract ALL architecture elements documented in this README ({source_label}).\n"
            "Return ONLY a JSON array of objects with keys: "
            "name, stereotype, package, confidence.\n"
            "Use exact element names and C4 package slugs from the README tables/sections.\n"
            "Containers → package technology. Components → package application.\n"
            "If none, return [].\n\n"
            f"{ontology}\nInstructions: {instructions[:500] or '(none)'}\n\n"
            f"Content:\n{text[:_MAX_FILE_CHARS]}"
        )
    else:
        user_content = (
            f"Extract architecture candidates from this {kind} ({source_label}).\n"
            "Return ONLY a JSON array of objects with keys: "
            "name, stereotype, package, confidence.\n"
            "Use docstring titles and section headings for names — not Python class names.\n"
            "If none, return [].\n\n"
            f"{ontology}\nInstructions: {instructions[:500] or '(none)'}\n\n"
            f"Content:\n{text[:_MAX_FILE_CHARS]}"
        )
    logger.info(
        "_llm_extract_text | request source=%s system_chars=%s user_chars=%s preview=%s",
        source_label,
        len(system),
        len(user_content),
        _preview(user_content),
    )
    response = llm.complete(
        messages=[LLMMessage(role="user", content=user_content)],
        system=system,
    ).content
    logger.info(
        "_llm_extract_text | response source=%s chars=%s preview=%s",
        source_label,
        len(response),
        _preview(response),
    )
    candidates = _parse_candidate_json(response) or []
    if source_label.endswith(_README_SOURCE) and not candidates:
        candidates = _parse_readme_architecture_table(text)
        if candidates:
            logger.info(
                "_llm_extract_text | source=%s branch=readme_table_fallback count=%s",
                source_label,
                len(candidates),
            )
    logger.info(
        "_llm_extract_text | source=%s kind=%s raw_candidates=%s parse_ok=%s",
        source_label,
        kind,
        len(candidates),
        candidates != [] or response.strip() in {"[]", ""},
    )
    return attach_source_paths(candidates, source_label)


def _cleanup(
    candidates: list[dict],
    element_slugs: set[str],
    package_slugs: set[str],
) -> list[dict]:
    logger.info(
        "_cleanup | entry raw_count=%s allowed_stereotypes=%s allowed_packages=%s summary=%s",
        len(candidates),
        sorted(element_slugs),
        sorted(package_slugs),
        _summarize_candidates(candidates),
    )
    accepted: list[dict] = []
    seen: dict[str, dict] = {}
    dropped_low_confidence = 0
    for raw in candidates:
        st = _slugify(str(raw.get("stereotype") or ""))
        if st == "external":
            logger.info(
                "_cleanup | drop external=%s reason=bootstrap_scope",
                raw.get("name"),
            )
            continue
        pkg = _normalize_package_slug(
            _slugify(str(raw.get("package") or "")),
            st,
            package_slugs,
        )
        if element_slugs and st not in element_slugs:
            logger.info(
                "_cleanup | drop unknown stereotype=%s name=%s reason=unknown_stereotype",
                st,
                raw.get("name"),
            )
            continue
        if pkg and package_slugs and pkg not in package_slugs:
            logger.info(
                "_cleanup | drop invalid package=%s name=%s stereotype=%s",
                pkg,
                raw.get("name"),
                st,
            )
            continue
        conf = float(raw.get("confidence", 0))
        if conf < 0.4:
            dropped_low_confidence += 1
            logger.info(
                "_cleanup | drop low_confidence=%s name=%s stereotype=%s reason=below_0.4",
                conf,
                raw.get("name"),
                st,
            )
            continue
        name = _humanize_element_name(str(raw.get("name") or ""))
        slug = _slugify(name)
        item = {**raw, "name": name, "stereotype": st, "package": pkg}
        prior = seen.get(slug)
        if prior is None or conf > float(prior.get("confidence", 0)):
            seen[slug] = item
    accepted.extend(seen.values())
    logger.info(
        "_cleanup | result accepted=%s dropped=%s deduped_slugs=%s low_confidence_drops=%s summary=%s",
        len(accepted),
        len(candidates) - len(accepted),
        len(seen),
        dropped_low_confidence,
        _summarize_candidates(accepted),
    )
    return accepted


def _reconcile(
    candidates: list[dict],
    by_slug: dict[str, dict],
    *,
    bootstrap_rescan: bool = False,
) -> DeltaBuckets:
    """Diff candidates against existing model elements.

    Bootstrap rescans bulk-delete all existing elements then re-add candidates.
    Update mode incrementally merges candidates without wiping matched slugs.
    """
    logger.info(
        "_reconcile | entry candidate_count=%s existing_slugs=%s bootstrap_rescan=%s",
        len(candidates),
        len(by_slug),
        bootstrap_rescan,
    )
    if bootstrap_rescan:
        buckets = _reconcile_bootstrap_rescan(candidates, by_slug)
    else:
        buckets = _reconcile_incremental(candidates, by_slug)
    logger.info(
        "_reconcile | result to_add=%s to_update=%s to_delete=%s unchanged=%s branch=%s",
        len(buckets.to_add),
        len(buckets.to_update),
        len(buckets.to_delete),
        len(buckets.unchanged),
        "bootstrap_rescan" if bootstrap_rescan else "incremental",
    )
    return buckets


_BOOTSTRAP_DELETE_CONFIDENCE = 1.0


def _reconcile_bootstrap_rescan(
    candidates: list[dict],
    by_slug: dict[str, dict],
) -> DeltaBuckets:
    """Bootstrap: delete every existing element, add all fresh candidates."""
    to_add: list[dict] = []
    for candidate in candidates:
        slug = _slugify(candidate["name"])
        to_add.append({**candidate, "slug": slug, "op": "add"})
    to_delete: list[dict] = []
    for slug, element in by_slug.items():
        to_delete.append(
            {
                "name": element.get("name"),
                "slug": slug,
                "element_id": element.get("id"),
                "confidence": _BOOTSTRAP_DELETE_CONFIDENCE,
                "op": "delete",
            }
        )
    return DeltaBuckets(to_add=to_add, to_delete=to_delete)


def _reconcile_incremental(
    candidates: list[dict],
    by_slug: dict[str, dict],
) -> DeltaBuckets:
    """Update/scout: merge candidates; delete slugs absent from the scan."""
    to_add: list[dict] = []
    to_update: list[dict] = []
    unchanged: list[dict] = []
    seen_slugs: set[str] = set()
    for candidate in candidates:
        slug = _slugify(candidate["name"])
        seen_slugs.add(slug)
        current = by_slug.get(slug)
        if current is None:
            to_add.append({**candidate, "slug": slug, "op": "add"})
        else:
            unchanged.append({**candidate, "slug": slug, "op": "unchanged"})
    to_delete: list[dict] = []
    for slug, element in by_slug.items():
        if slug in seen_slugs:
            continue
        to_delete.append(
            {
                "name": element.get("name"),
                "slug": slug,
                "element_id": element.get("id"),
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


def _format_discovery_output_lines(
    *,
    element_count: int,
    relationship_count: int,
    buckets: DeltaBuckets,
    trigger: str,
    bootstrap_rescan: bool,
) -> list[str]:
    """Format stable CLI log lines for bootstrap vs update runs."""
    lines = [
        "building ModelSummary",
        f"found {element_count} existing elements",
        f"found {relationship_count} relationships",
        f"to_add: {len(buckets.to_add)}",
    ]
    if not bootstrap_rescan:
        lines.extend(
            [
                f"to_update: {len(buckets.to_update)}",
                f"to_delete: {len(buckets.to_delete)}",
                f"unchanged: {len(buckets.unchanged)}",
            ]
        )
    elif buckets.to_delete:
        lines.append(f"to_delete: {len(buckets.to_delete)}")
    lines.append(f"trigger: ratatosk {trigger}")
    return lines


def _all_bucket_operations(buckets: DeltaBuckets, *, bootstrap_rescan: bool = False) -> list[dict]:
    delete_ops: list[dict] = []
    for item in buckets.to_delete:
        delete_ops.append(
            {
                "op_type": "delete_element",
                "detail": {
                    "element_id": item.get("element_id"),
                    "name": item.get("name"),
                },
                "confidence": float(
                    item.get(
                        "confidence", _BOOTSTRAP_DELETE_CONFIDENCE if bootstrap_rescan else 0.5
                    )
                ),
            }
        )
    add_ops: list[dict] = []
    for item in buckets.to_add:
        add_ops.append(
            {
                "op_type": "add_element",
                "detail": {
                    "name": item["name"],
                    "stereotype_slug": _slugify(item.get("stereotype", "container")),
                    "package_slug": _slugify(item.get("package", "technology")),
                },
                "confidence": float(item.get("confidence", 0.9)),
            }
        )
    update_ops: list[dict] = []
    for item in buckets.to_update:
        update_ops.append(
            {
                "op_type": "update_element",
                "detail": {
                    "element_id": item.get("element_id"),
                    "fields": item.get("fields") or {},
                },
                "confidence": float(item.get("confidence", 0.85)),
            }
        )
    if bootstrap_rescan:
        return delete_ops + add_ops + update_ops
    return add_ops + update_ops + delete_ops


def _buckets_to_operations(buckets: DeltaBuckets, threshold: float) -> list[dict]:
    """Kept for callers that want only above-threshold ops."""
    all_ops = _all_bucket_operations(buckets)
    return [op for op in all_ops if float(op.get("confidence", 0)) >= threshold]


def _prioritize_targets(tree: list[str], targets: list[str]) -> list[str]:
    """Backward-compatible wrapper; prefer ``ratatosk.discovery.limits.prioritize_targets``."""
    return prioritize_targets(tree, targets, DiscoveryLimits())


def _normalize_package_slug(pkg: str, stereotype: str, package_slugs: set[str]) -> str:
    """Map file-path packages to C4 package slugs using stereotype defaults."""
    if pkg in package_slugs:
        return pkg
    fallback = _STEREOTYPE_DEFAULT_PACKAGE.get(stereotype, "")
    if fallback and fallback in package_slugs:
        logger.info(
            "_normalize_package_slug | input=%s stereotype=%s resolved=%s branch=stereotype_default",
            pkg or "(empty)",
            stereotype,
            fallback,
        )
        return fallback
    return pkg


def _humanize_element_name(name: str) -> str:
    """BillingWorker → Billing Worker when LLM returns class names."""
    text = name.strip()
    if not text or " " in text:
        return text
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)


def _parse_readme_architecture_table(text: str) -> list[dict]:
    """
    Parse README markdown tables listing C4 elements (sample_webapp fixture shape).

    :param text: README body.
    :return: Candidate dicts with name, stereotype, package, confidence.
    """
    candidates: list[dict] = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        parts = [part.strip() for part in line.split("|") if part.strip()]
        if len(parts) < 2:
            continue
        if parts[0].lower() in {"element", "name"} or parts[1].lower() == "stereotype":
            continue
        if set(parts[0]) <= {"-", ":"}:
            continue
        name = parts[0].strip("*").strip()
        stereotype = _slugify(parts[1])
        if stereotype not in {"container", "component", "system", "person"}:
            continue
        package = _STEREOTYPE_DEFAULT_PACKAGE.get(stereotype, "technology")
        candidates.append(
            {
                "name": name,
                "stereotype": stereotype,
                "package": package,
                "confidence": 0.95,
            }
        )
    return candidates


def _summarize_candidates(candidates: list[dict]) -> dict[str, int]:
    """Count candidates by stereotype slug for log summaries."""
    counts: dict[str, int] = {}
    for item in candidates:
        key = _slugify(str(item.get("stereotype") or "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _summarize_op_types(operations: list[dict]) -> dict[str, int]:
    """Count proposed ChangeSet operations by op_type."""
    counts: dict[str, int] = {}
    for op in operations:
        key = str(op.get("op_type") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _preview(text: str, limit: int = _PREVIEW_CHARS) -> str:
    """Single-line preview for discovery log lines."""
    collapsed = text.replace("\n", "\\n")
    if len(collapsed) <= limit:
        return collapsed
    return f"{collapsed[:limit]}…({len(text)} chars total)"


def _slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")
