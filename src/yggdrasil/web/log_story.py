"""Assemble a readable per-request story from ``logs/app.log`` JSON lines."""

from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any

_MAX_BYTES = 2_000_000
_MAX_REQUESTS = 40


def load_recent_requests(log_path: Any) -> list[dict[str, Any]]:
    """
    Return recent request summaries, newest first.

    :param log_path: Path to ``app.log``. Example: ``Path("logs/app.log")``.
    :return: Dicts with ``request_id``, ``path``, ``started``, ``entry_count``.
    """
    grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for entry in _read_json_lines(log_path):
        request_id = entry.get("request_id")
        if not request_id:
            continue
        bucket = grouped.setdefault(
            str(request_id),
            {
                "request_id": str(request_id),
                "path": entry.get("path") or "",
                "started": entry.get("timestamp") or "",
                "entry_count": 0,
            },
        )
        bucket["entry_count"] += 1
        if not bucket["path"] and entry.get("path"):
            bucket["path"] = entry["path"]
        if not bucket["started"] and entry.get("timestamp"):
            bucket["started"] = entry["timestamp"]
    return list(reversed(list(grouped.values())))[:_MAX_REQUESTS]


def load_request_story(log_path: Any, request_id: str) -> dict[str, Any] | None:
    """
    Return one request's ordered log entries, or None when none match.

    :param log_path: Path to ``app.log``.
    :param request_id: Correlation id. Example: ``"req-7f3a"``.
    :return: Story dict with ``request_id``, ``path``, ``entries``.
    """
    entries = [
        _viewer_entry(raw)
        for raw in _read_json_lines(log_path)
        if str(raw.get("request_id") or "") == request_id
    ]
    if not entries:
        return None
    path = next((item["path"] for item in entries if item.get("path")), "")
    return {"request_id": request_id, "path": path, "entries": entries}


def _read_json_lines(log_path: Any) -> list[dict[str, Any]]:
    """Read the tail of a JSON-lines log file."""
    path = log_path
    if not getattr(path, "exists", lambda: False)() or path.stat().st_size == 0:
        return []
    raw = _read_tail(path)
    entries: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
    return entries


def _read_tail(path: Any) -> str:
    """Read up to ``_MAX_BYTES`` from the end of ``path``."""
    size = path.stat().st_size
    with path.open("r", encoding="utf-8") as handle:
        if size > _MAX_BYTES:
            handle.seek(size - _MAX_BYTES)
            handle.readline()
        return handle.read()


def _viewer_entry(raw: dict[str, Any]) -> dict[str, Any]:
    """Shape one JSON log object for the story template."""
    level = str(raw.get("level") or "info").lower()
    context = raw.get("context")
    if not isinstance(context, dict):
        context = {}
    module = raw.get("code_module") or raw.get("module") or raw.get("logger") or ""
    thread = raw.get("code_thread") or raw.get("thread") or ""
    line = raw.get("code_line") if raw.get("code_line") is not None else raw.get("line") or ""
    return {
        "timestamp": raw.get("timestamp") or "",
        "clock": _clock(str(raw.get("timestamp") or "")),
        "level": level,
        "event": raw.get("event") or "",
        "module": module,
        "thread": thread,
        "line": line,
        "path": raw.get("path") or "",
        "context": context,
        "payload_json": json.dumps(
            {
                "module": module,
                "thread": thread,
                "line": line,
                "logger": raw.get("logger") or "",
                "context": context,
            },
            indent=2,
            default=str,
        ),
    }


def _clock(timestamp: str) -> str:
    """Turn an ISO timestamp into ``HH:MM:SS.mmm``."""
    if "T" not in timestamp:
        return timestamp
    clock = timestamp.split("T", 1)[1]
    clock = clock.replace("Z", "")
    if "." in clock:
        head, frac = clock.split(".", 1)
        return f"{head}.{frac[:3]}"
    return clock
