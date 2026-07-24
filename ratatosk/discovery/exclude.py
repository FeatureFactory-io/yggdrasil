"""Path exclusion helpers for Ratatosk filesystem discovery."""

from __future__ import annotations

import fnmatch
import logging

logger = logging.getLogger("ratatosk.discovery.exclude")

# Always skipped during bootstrap — IDE/playbook noise, not architecture sources.
_BOOTSTRAP_IMPLICIT_EXCLUDES: tuple[str, ...] = (
    ".cursor/**",
    "docs/features/**",
    "tests/fixtures/**",
    "mockups/**",
)


def normalize_exclude_patterns(raw: str | list[str] | None) -> list[str]:
    """
    Parse comma-separated or list exclude patterns.

    :param raw: CSV string or list from CLI/env/YAML.
    :return: Non-empty stripped patterns.
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [part.strip() for part in raw.split(",")]
    else:
        parts = [str(part).strip() for part in raw]
    patterns = [part for part in parts if part]
    logger.info("normalize_exclude_patterns | count=%s patterns=%s", len(patterns), patterns)
    return patterns


def merge_bootstrap_exclude_patterns(patterns: list[str]) -> list[str]:
    """
    Merge operator exclude patterns with bootstrap implicit skips.

    Implicit excludes (``.cursor/**``) apply on every bootstrap scan so
    Cursor playbooks/rules are not fed to Ratatosk NER.

    :param patterns: Operator-provided exclude patterns.
    :return: De-duplicated merged pattern list.
    """
    merged: list[str] = []
    for pattern in [*patterns, *_BOOTSTRAP_IMPLICIT_EXCLUDES]:
        cleaned = pattern.strip()
        if cleaned and cleaned not in merged:
            merged.append(cleaned)
    logger.info(
        "merge_bootstrap_exclude_patterns | operator_count=%s implicit=%s merged_count=%s "
        "merged_patterns=%s",
        len(patterns),
        list(_BOOTSTRAP_IMPLICIT_EXCLUDES),
        len(merged),
        merged,
    )
    return merged


def path_is_excluded(rel_path: str, patterns: list[str]) -> bool:
    """
    Return True when a relative repo path matches an exclude pattern.

    Supports directory prefixes, ``dir/**`` prefixes, and fnmatch globs.

    :param rel_path: Repository-relative path using forward slashes.
    :param patterns: Normalized exclude patterns.
    :return: Whether the path should be skipped.
    """
    if not patterns:
        return False
    normalized = rel_path.replace("\\", "/")
    for pattern in patterns:
        candidate = pattern.strip()
        if not candidate:
            continue
        if candidate.endswith("/**"):
            prefix = candidate[:-3].rstrip("/")
            if normalized == prefix or normalized.startswith(f"{prefix}/"):
                return True
            continue
        if "*" in candidate or "?" in candidate or "[" in candidate:
            if fnmatch.fnmatch(normalized, candidate):
                return True
            continue
        prefix = candidate if candidate.endswith("/") else f"{candidate}/"
        if normalized.startswith(prefix) or normalized == candidate.rstrip("/"):
            return True
    return False
