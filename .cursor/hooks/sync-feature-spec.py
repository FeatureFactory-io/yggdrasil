#!/usr/bin/env python3
"""Cursor hook: warn when docs/features and features/at|e2e promoted twins drift.

Modes (argv[1]):
  after-edit  - afterFileEdit / afterTabFileEdit stdin JSON
  post-tool   - postToolUse stdin JSON (Write / StrReplace / EditNotebook)
  stop        - stop stdin JSON; emits followup_message when drift is pending

Policy: docs/features = living spec; features/at|e2e = CI runners.
Only nudge when a promoted twin already exists. No auto-copy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

STATE_FILE = Path(__file__).resolve().parent / ".feature-sync-state.json"
RUNNER_DIRS = ("features/at", "features/e2e")
DOCS_ROOT = Path("docs/features")


def _read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _repo_root(cwd: str | None) -> Path:
    if cwd:
        return Path(cwd).resolve()
    return Path.cwd().resolve()


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_gherkin(text: str) -> str:
    """Compare scenario bodies; ignore comment-only lines and trailing whitespace."""
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if not stripped:
            continue
        if stripped.lstrip().startswith("#"):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def _read_normalized(path: Path) -> str | None:
    if not path.is_file():
        return None
    return _normalize_gherkin(path.read_text(encoding="utf-8"))


def _is_docs_feature(rel: str) -> bool:
    return rel.startswith("docs/features/") and rel.endswith(".feature")


def _is_runner_feature(rel: str) -> bool:
    return rel.startswith("features/at/") or rel.startswith("features/e2e/")


def _basename(rel: str) -> str:
    return Path(rel).name


def _find_docs_twins(root: Path, basename: str) -> list[Path]:
    docs = root / DOCS_ROOT
    if not docs.is_dir():
        return []
    return sorted(docs.rglob(basename))


def _find_runner_twins(root: Path, basename: str) -> list[Path]:
    twins: list[Path] = []
    for runner in RUNNER_DIRS:
        candidate = root / runner / basename
        if candidate.is_file():
            twins.append(candidate)
    return twins


def _classify_edit(root: Path, rel: str) -> list[dict[str, str]]:
    """Return drift records for an edited feature file."""
    basename = _basename(rel)
    records: list[dict[str, str]] = []

    if _is_docs_feature(rel):
        source = root / rel
        for twin in _find_runner_twins(root, basename):
            twin_rel = _rel(twin, root)
            source_norm = _read_normalized(source)
            twin_norm = _read_normalized(twin)
            if source_norm is None or twin_norm is None:
                continue
            if source_norm != twin_norm:
                records.append(
                    {
                        "source": rel,
                        "target": twin_rel,
                        "direction": "spec_to_runner",
                        "message": (
                            f"Spec `{rel}` was edited but promoted runner `{twin_rel}` "
                            f"is out of sync. Update the runner copy in the same change "
                            f"(preserve runner-only @tags). See "
                            f"docs/architecture/test-architecture.md §4."
                        ),
                    }
                )
        return records

    if _is_runner_feature(rel):
        source = root / rel
        for twin in _find_docs_twins(root, basename):
            twin_rel = _rel(twin, root)
            source_norm = _read_normalized(source)
            twin_norm = _read_normalized(twin)
            if source_norm is None or twin_norm is None:
                continue
            if source_norm != twin_norm:
                records.append(
                    {
                        "source": rel,
                        "target": twin_rel,
                        "direction": "runner_to_spec",
                        "message": (
                            f"Runner `{rel}` was edited but living spec `{twin_rel}` "
                            f"is out of sync. Update the docs copy in the same change. "
                            f"See docs/architecture/test-architecture.md §4."
                        ),
                    }
                )
        return records

    return records


def _extract_path_from_post_tool(payload: dict[str, Any], root: Path) -> str | None:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None

    path_value = tool_input.get("path") or tool_input.get("target_notebook")
    if not path_value:
        return None

    path = Path(str(path_value))
    if not path.is_absolute():
        path = (root / path).resolve()
    rel = _rel(path, root)
    if not (rel.endswith(".feature") or _is_docs_feature(rel) or _is_runner_feature(rel)):
        return None
    return rel


def _load_state() -> dict[str, Any]:
    if not STATE_FILE.is_file():
        return {"pending": []}
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"pending": []}
    if "pending" not in data or not isinstance(data["pending"], list):
        data["pending"] = []
    return data


def _save_state(data: dict[str, Any]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _merge_pending(records: list[dict[str, str]]) -> None:
    if not records:
        return
    state = _load_state()
    pending: list[dict[str, str]] = state["pending"]
    seen = {(item["source"], item["target"]) for item in pending}
    for record in records:
        key = (record["source"], record["target"])
        if key in seen:
            for item in pending:
                if item["source"] == record["source"] and item["target"] == record["target"]:
                    item["message"] = record["message"]
            continue
        pending.append(record)
        seen.add(key)
    state["pending"] = pending
    _save_state(state)


def _clear_state() -> None:
    if STATE_FILE.is_file():
        STATE_FILE.unlink()


def mode_after_edit(payload: dict[str, Any]) -> None:
    file_path = payload.get("file_path")
    if not file_path:
        return
    root = _repo_root(payload.get("cwd"))
    rel = _rel(Path(str(file_path)), root)
    if not (_is_docs_feature(rel) or _is_runner_feature(rel)):
        return
    records = _classify_edit(root, rel)
    _merge_pending(records)


def mode_post_tool(payload: dict[str, Any]) -> None:
    root = _repo_root(payload.get("cwd"))
    rel = _extract_path_from_post_tool(payload, root)
    if not rel:
        print("{}")
        return
    records = _classify_edit(root, rel)
    _merge_pending(records)
    if records:
        message = records[0]["message"]
        print(json.dumps({"additional_context": message}))
        return
    print("{}")


def mode_stop(payload: dict[str, Any]) -> None:
    status = payload.get("status", "completed")
    if status != "completed":
        _clear_state()
        print("{}")
        return

    state = _load_state()
    pending: list[dict[str, str]] = state.get("pending", [])
    if not pending:
        print("{}")
        return

    lines = [
        "Feature spec/runner sync required before finishing:",
        "",
    ]
    for item in pending[:5]:
        lines.append(f"- {item['message']}")
    if len(pending) > 5:
        lines.append(f"- ...and {len(pending) - 5} more drift pair(s).")

    lines.extend(
        [
            "",
            "Update both copies in the same change. Do not delete from docs/features/.",
            "Reference: docs/architecture/test-architecture.md §4.",
        ]
    )
    followup = "\n".join(lines)
    _clear_state()
    print(json.dumps({"followup_message": followup}))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "after-edit"
    payload = _read_stdin_json()

    if mode == "after-edit":
        mode_after_edit(payload)
        print("{}")
    elif mode == "post-tool":
        mode_post_tool(payload)
    elif mode == "stop":
        mode_stop(payload)
    else:
        print("{}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
