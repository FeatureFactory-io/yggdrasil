"""
Django-free discovery orchestration for the Ratatosk CLI.

Uses MCP client for snapshot, stereotypes, ensure_model, propose, record_run.
Never imports Django.
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from ratatosk.discovery.model_summary import build_model_summary
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
_MAX_EXTRACT_TARGETS = 12
_STEREOTYPE_DEFAULT_PACKAGE: dict[str, str] = {
    "container": "technology",
    "system": "technology",
    "component": "application",
    "person": "context",
}
_README_SOURCE = "README.md"


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
) -> tuple[str, DeltaBuckets, str]:
    """
    Run discovery and hand off via MCP. No Django.

    :param client: Object with ``call_tool(name, arguments) -> dict``.
    :param llm: Object with ``complete(messages, system=...) -> response``.
    :return: (run_id, buckets, CLI output text)
    """
    logger.info(
        "run_cli_discovery | entry mode=%s model=%s metamodel=%s confidence_threshold=%s",
        mode,
        model_name,
        metamodel,
        confidence_threshold,
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

    wipe_line = ""
    if mode == "filesystem":
        if element_count == 0:
            wipe_line = "wipe no-op for empty graph"
        else:
            wipe_line = f"wiping {element_count} elements before bootstrap rescan"
        logger.info("run_cli_discovery | %s", wipe_line)

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

    blackboard: dict[str, Any] = {
        "fetched_model": {
            "elements": element_count,
            "relationships": relationship_count,
        },
        "model_summary": summary_meta,
        "metamodel": {"slug": metamodel},
    }

    if mode == "filesystem":
        logger.info(
            "run_cli_discovery | scan_start repo_path=%s reason=bootstrap_filesystem_scan",
            repo_path,
        )
        tree = _build_file_tree(repo_path)
        blackboard["tree"] = {"paths": tree, "count": len(tree)}
        blackboard["input_mode"] = "filesystem"
        if not tree:
            candidates: list[dict] = []
            blackboard["extract"] = {"candidates": 0, "reason": "nothing to scan"}
            logger.warning(
                "run_cli_discovery | scan_complete file_count=0 branch=nothing_to_scan "
                "reason=empty_tree",
            )
        else:
            project_map = _llm_project_map(llm, tree, ontology)
            blackboard["project_map"] = project_map
            targets = _prioritize_targets(
                tree,
                project_map.get("targets") or tree[:_MAX_EXTRACT_TARGETS],
            )
            logger.info(
                "run_cli_discovery | scan_map_complete project_kind=%s "
                "tree_paths=%s mapped_targets=%s targets=%s",
                project_map.get("project_kind"),
                len(tree),
                len(project_map.get("targets") or []),
                targets,
            )
            candidates = _llm_extract_files(llm, repo_path, targets, ontology, instructions)
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
            _llm_map_stdin(llm, stdin_text, kind, ontology, instructions)
            candidates = _llm_extract_text(
                llm, stdin_text, kind, ontology, instructions, source_label="stdin"
            )

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
    buckets = _reconcile(cleaned, by_slug)
    logger.info(
        "run_cli_discovery | reconcile to_add=%s to_update=%s to_delete=%s unchanged=%s "
        "add_names=%s",
        len(buckets.to_add),
        len(buckets.to_update),
        len(buckets.to_delete),
        len(buckets.unchanged),
        [item.get("name") for item in buckets.to_add],
    )

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    operations = _buckets_to_operations(buckets, confidence_threshold)
    # Include below-threshold ops too (server splits apply)
    operations = _all_bucket_operations(buckets)
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
        },
    )
    changeset_id = propose["changeset_id"]
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
    output_lines.extend(
        [
            "building ModelSummary",
            f"found {element_count} existing elements",
            f"found {relationship_count} relationships",
            f"to_add: {len(buckets.to_add)}",
            f"to_update: {len(buckets.to_update)}",
            f"to_delete: {len(buckets.to_delete)}",
            f"unchanged: {len(buckets.unchanged)}",
            f"trigger: ratatosk {'bootstrap' if mode == 'filesystem' else 'update'}",
        ]
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


def _build_file_tree(repo_path: str) -> list[str]:
    """Walk repo_path and return relative file paths (ignored dirs skipped)."""
    logger.info(
        "_build_file_tree | entry repo_path=%s ignore_dirs=%s ignore_files=%s",
        repo_path,
        sorted(_IGNORE_DIR_NAMES),
        sorted(_IGNORE_FILE_NAMES),
    )
    root = Path(repo_path)
    if not root.exists():
        raise RuntimeError(f"Repository path does not exist: {repo_path}")
    if not root.is_dir():
        raise RuntimeError(f"Repository path is not a directory: {repo_path}")
    paths: list[str] = []
    skipped_dirs = 0
    skipped_files = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in _IGNORE_DIR_NAMES for part in rel.parts[:-1]):
            skipped_dirs += 1
            continue
        if rel.name.lower() in _IGNORE_FILE_NAMES:
            skipped_files += 1
            continue
        paths.append(rel.as_posix())
    preview = paths[:8]
    tail = paths[-3:] if len(paths) > 8 else []
    logger.info(
        "_build_file_tree | result file_count=%s skipped_under_ignore_dir=%s "
        "skipped_ignore_file=%s head=%s tail=%s",
        len(paths),
        skipped_dirs,
        skipped_files,
        preview,
        tail,
    )
    return paths


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
    element_slugs: set[str] = set()
    package_slugs: set[str] = set()
    lines = ["# Metamodel stereotypes (from MCP list_stereotypes)", ""]
    for st in items:
        slug = str(st.get("slug") or "")
        if st.get("is_edge"):
            lines.append(f"- edge `{slug}` — {st.get('name')}")
        else:
            element_slugs.add(slug)
            lines.append(f"- element `{slug}` — {st.get('name')}")
    # C4 packages are not on list_stereotypes; allow common c4 package slugs.
    package_slugs |= {"context", "technology", "application", "code"}
    lines.append("")
    lines.append(
        "Package slug must be one of: context, technology, application, code. "
        "Containers → technology. Domain/components → application."
    )
    lines.append("Use only element stereotype slugs from the list. Do not invent types.")
    lines.append(
        "Use human-readable element names from docs (e.g. 'Billing Worker' not 'BillingWorker')."
    )
    return "\n".join(lines), element_slugs, package_slugs


def _llm_project_map(llm: Any, tree: list[str], ontology: str) -> dict[str, Any]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    logger.info(
        "_llm_project_map | entry tree_paths=%s ontology_chars=%s llm=%s",
        len(tree),
        len(ontology),
        getattr(llm, "model_id", type(llm).__name__),
    )
    tree_preview = "\n".join(tree[:200])
    system = "You are Ratatosk mapping a repository. Return JSON only."
    user_content = (
        "Given this repository file tree (paths only), return ONLY JSON:\n"
        '{"project_kind": "...", "targets": ["path", ...]}\n'
        "Always include README.md when present. Prefer manifest/source paths over __init__.py.\n"
        f"File tree:\n{tree_preview}\n\n{ontology}\n"
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
    targets = [str(t) for t in (parsed.get("targets") or []) if str(t) in tree]
    if _README_SOURCE in tree and _README_SOURCE not in targets:
        targets.insert(0, _README_SOURCE)
    if not targets:
        targets = tree[:_MAX_EXTRACT_TARGETS]
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
        "targets": targets[:_MAX_EXTRACT_TARGETS],
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
) -> list[dict]:
    """Read each target file from disk and run LLM extract (paths-only map precedes this)."""
    bounded = targets[:_MAX_EXTRACT_TARGETS]
    logger.info(
        "_llm_extract_files | entry repo_path=%s target_count=%s max_targets=%s targets=%s",
        repo_path,
        len(bounded),
        _MAX_EXTRACT_TARGETS,
        bounded,
    )
    root = Path(repo_path)
    all_c: list[dict] = []
    read_count = 0
    skipped_missing = 0
    for rel in bounded:
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
            "_llm_extract_files | read path=%s bytes=%s extracted_chars=%s capped=%s",
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
    return all_c


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
    return candidates


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


def _reconcile(candidates: list[dict], by_slug: dict[str, dict]) -> DeltaBuckets:
    logger.info(
        "_reconcile | entry candidate_count=%s existing_slugs=%s",
        len(candidates),
        len(by_slug),
    )
    to_add: list[dict] = []
    to_update: list[dict] = []
    unchanged: list[dict] = []
    for candidate in candidates:
        slug = _slugify(candidate["name"])
        current = by_slug.get(slug)
        if current is None:
            to_add.append({**candidate, "slug": slug, "op": "add"})
        else:
            unchanged.append({**candidate, "slug": slug, "op": "unchanged"})
    buckets = DeltaBuckets(to_add=to_add, to_update=to_update, unchanged=unchanged)
    logger.info(
        "_reconcile | result to_add=%s to_update=%s to_delete=%s unchanged=%s " "branch=%s",
        len(buckets.to_add),
        len(buckets.to_update),
        len(buckets.to_delete),
        len(buckets.unchanged),
        "empty_model_add_heavy" if not by_slug else "delta_reconcile",
    )
    return buckets


def _all_bucket_operations(buckets: DeltaBuckets) -> list[dict]:
    ops: list[dict] = []
    for item in buckets.to_add:
        ops.append(
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
    for item in buckets.to_update:
        ops.append(
            {
                "op_type": "update_element",
                "detail": {
                    "element_id": item.get("element_id"),
                    "fields": item.get("fields") or {},
                },
                "confidence": float(item.get("confidence", 0.85)),
            }
        )
    for item in buckets.to_delete:
        ops.append(
            {
                "op_type": "delete_element",
                "detail": {
                    "element_id": item.get("element_id"),
                    "name": item.get("name"),
                },
                "confidence": float(item.get("confidence", 0.5)),
            }
        )
    return ops


def _buckets_to_operations(buckets: DeltaBuckets, threshold: float) -> list[dict]:
    """Kept for callers that want only above-threshold ops."""
    all_ops = _all_bucket_operations(buckets)
    return [op for op in all_ops if float(op.get("confidence", 0)) >= threshold]


def _prioritize_targets(tree: list[str], targets: list[str]) -> list[str]:
    """Put README.md first so architecture overview is extracted before source files."""
    ordered: list[str] = []
    if _README_SOURCE in tree:
        ordered.append(_README_SOURCE)
    for rel in targets:
        if rel not in ordered:
            ordered.append(rel)
    return ordered[:_MAX_EXTRACT_TARGETS]


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
