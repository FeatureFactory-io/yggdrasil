"""
Django-free discovery orchestration for the Ratatosk CLI.

Uses MCP client for snapshot, stereotypes, ensure_model, propose, record_run.
Never imports Django.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("ratatosk.discovery.runner")

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
_MAX_FILE_CHARS = 8_000


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
        "run_cli_discovery | mode=%s model=%s metamodel=%s",
        mode,
        model_name,
        metamodel,
    )
    ensured = client.call_tool("ensure_model", {"model": model_name, "metamodel": metamodel})
    model_slug = str(ensured["slug"])

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

    stereotypes = client.call_tool("list_stereotypes", {"model": model_slug})
    ontology, element_slugs, package_slugs = _guidance_from_stereotypes(
        stereotypes.get("items") or []
    )

    blackboard: dict[str, Any] = {
        "fetched_model": {
            "elements": element_count,
            "relationships": relationship_count,
        },
        "metamodel": {"slug": metamodel},
    }

    if mode == "filesystem":
        tree = _build_file_tree(repo_path)
        blackboard["tree"] = {"paths": tree, "count": len(tree)}
        blackboard["input_mode"] = "filesystem"
        if not tree:
            candidates: list[dict] = []
            blackboard["extract"] = {"candidates": 0, "reason": "nothing to scan"}
        else:
            project_map = _llm_project_map(llm, tree, ontology)
            blackboard["project_map"] = project_map
            targets = project_map.get("targets") or tree[:_MAX_EXTRACT_TARGETS]
            candidates = _llm_extract_files(llm, repo_path, targets, ontology, instructions)
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
    buckets = _reconcile(cleaned, by_slug)

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    operations = _buckets_to_operations(buckets, confidence_threshold)
    # Include below-threshold ops too (server splits apply)
    operations = _all_bucket_operations(buckets)

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

    output_lines = [
        "fetching existing model state via MCP",
        f"found {element_count} existing elements",
        f"found {relationship_count} relationships",
        f"to_add: {len(buckets.to_add)}",
        f"to_update: {len(buckets.to_update)}",
        f"to_delete: {len(buckets.to_delete)}",
        f"unchanged: {len(buckets.unchanged)}",
        f"trigger: ratatosk {'bootstrap' if mode == 'filesystem' else 'update'}",
    ]
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
    root = Path(repo_path)
    if not root.exists():
        raise RuntimeError(f"Repository path does not exist: {repo_path}")
    if not root.is_dir():
        raise RuntimeError(f"Repository path is not a directory: {repo_path}")
    paths: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in _IGNORE_DIR_NAMES for part in rel.parts[:-1]):
            continue
        if rel.name.lower() in _IGNORE_FILE_NAMES:
            continue
        paths.append(rel.as_posix())
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
    lines.append("Use only element stereotype slugs from the list. Do not invent types.")
    return "\n".join(lines), element_slugs, package_slugs


def _llm_project_map(llm: Any, tree: list[str], ontology: str) -> dict[str, Any]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    tree_preview = "\n".join(tree[:200])
    response = llm.complete(
        messages=[
            LLMMessage(
                role="user",
                content=(
                    "Given this repository file tree (paths only), return ONLY JSON:\n"
                    '{"project_kind": "...", "targets": ["path", ...]}\n'
                    f"File tree:\n{tree_preview}\n\n{ontology}\n"
                ),
            )
        ],
        system="You are Ratatosk mapping a repository. Return JSON only.",
    ).content
    parsed = _parse_json_object(response) or {}
    targets = [str(t) for t in (parsed.get("targets") or []) if str(t) in tree]
    if not targets:
        targets = tree[:_MAX_EXTRACT_TARGETS]
    return {
        "project_kind": str(parsed.get("project_kind") or "unknown"),
        "targets": targets[:_MAX_EXTRACT_TARGETS],
    }


def _llm_map_stdin(
    llm: Any, blob: str, kind: str, ontology: str, instructions: str
) -> dict[str, Any]:
    from ratatosk.discovery.scripted_llm import LLMMessage

    response = llm.complete(
        messages=[
            LLMMessage(
                role="user",
                content=(
                    f"Classify this {kind} stdin for architecture extraction.\n"
                    f"{ontology}\nInstructions: {instructions[:500] or '(none)'}\n"
                    f"Stdin:\n{blob[:4000]}"
                ),
            )
        ],
        system="You are Ratatosk mapping stdin. JSON only.",
    ).content
    return _parse_json_object(response) or {}


def _llm_extract_files(
    llm: Any,
    repo_path: str,
    targets: list[str],
    ontology: str,
    instructions: str,
) -> list[dict]:
    root = Path(repo_path)
    all_c: list[dict] = []
    for rel in targets[:_MAX_EXTRACT_TARGETS]:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")[:_MAX_FILE_CHARS]
        all_c.extend(_llm_extract_text(llm, text, "file", ontology, instructions, source_label=rel))
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

    response = llm.complete(
        messages=[
            LLMMessage(
                role="user",
                content=(
                    f"Extract architecture candidates from this {kind} ({source_label}).\n"
                    "Return ONLY a JSON array of objects with keys: "
                    "name, stereotype, package, confidence.\n"
                    "If none, return [].\n\n"
                    f"{ontology}\nInstructions: {instructions[:500] or '(none)'}\n\n"
                    f"Content:\n{text[:_MAX_FILE_CHARS]}"
                ),
            )
        ],
        system="You are Ratatosk. Use only listed stereotype slugs. Prefer [] over inventing.",
    ).content
    return _parse_candidate_json(response) or []


def _cleanup(
    candidates: list[dict],
    element_slugs: set[str],
    package_slugs: set[str],
) -> list[dict]:
    accepted: list[dict] = []
    seen: dict[str, dict] = {}
    for raw in candidates:
        st = _slugify(str(raw.get("stereotype") or ""))
        pkg = _slugify(str(raw.get("package") or ""))
        if element_slugs and st not in element_slugs:
            logger.info(
                "_cleanup | drop unknown stereotype=%s name=%s reason=unknown_stereotype",
                st,
                raw.get("name"),
            )
            continue
        if pkg and package_slugs and pkg not in package_slugs:
            continue
        conf = float(raw.get("confidence", 0))
        if conf < 0.4:
            continue
        slug = _slugify(str(raw["name"]))
        item = {**raw, "stereotype": st, "package": pkg}
        prior = seen.get(slug)
        if prior is None or conf > float(prior.get("confidence", 0)):
            seen[slug] = item
    accepted.extend(seen.values())
    return accepted


def _reconcile(candidates: list[dict], by_slug: dict[str, dict]) -> DeltaBuckets:
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
    return DeltaBuckets(to_add=to_add, to_update=to_update, unchanged=unchanged)


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


def _slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def _parse_candidate_json(raw: str) -> list[dict] | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    if not isinstance(data, list):
        return None
    return [item for item in data if isinstance(item, dict) and item.get("name")]


def _parse_json_object(raw: str) -> dict | None:
    text = (raw or "").strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None
    return data if isinstance(data, dict) else None
