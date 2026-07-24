"""Deterministic pre-filter for bootstrap candidates (Phase D0)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from fnmatch import fnmatch

logger = logging.getLogger("ratatosk.discovery.prefilter")

_NOISE_SOURCE_GLOBS: tuple[str, ...] = (
    "docs/features/**",
    "tests/**",
    "mockups/**",
    "*.feature",
)

_TEST_LIB_NAMES: frozenset[str] = frozenset(
    {
        "pytest",
        "pytest-django",
        "pytest-watch",
        "behave",
        "behave-django",
        "playwright",
        "aws_cdk.assertions",
        "django test client",
    }
)

_TEST_SOURCE_GLOBS: tuple[str, ...] = (
    "tests/**",
    "pyproject.toml",
    "requirements*.txt",
)


@dataclass
class PrefilterResult:
    """Outcome of deterministic candidate pre-filtering."""

    kept: list[dict] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    cluster_hints: dict[str, list[str]] = field(default_factory=dict)


def _normalize_cluster_key(name: str) -> str:
    lowered = name.strip().lower()
    for token in ("postgresql", "postgres", "postgre"):
        if token in lowered:
            return "postgres"
    if "redis" in lowered:
        return "redis"
    if "backend" in lowered:
        return "backend"
    if "mcp" in lowered and "facade" in lowered:
        return "mcp_facade"
    return lowered[:40]


def _path_matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(path, pattern) for pattern in patterns)


def _only_noise_sources(source_paths: list[str]) -> bool:
    if not source_paths:
        return False
    return all(_path_matches_any(path, _NOISE_SOURCE_GLOBS) for path in source_paths)


def _is_test_lib_noise(candidate: dict) -> bool:
    name = str(candidate.get("name") or "").strip().lower()
    if name not in _TEST_LIB_NAMES and name.replace("_", " ") not in _TEST_LIB_NAMES:
        return False
    paths = list(candidate.get("source_paths") or [])
    return not paths or all(_path_matches_any(p, _TEST_SOURCE_GLOBS) for p in paths)


def prefilter_candidates(candidates: list[dict]) -> PrefilterResult:
    """
    Apply path-class and test-lib rejection rules before Sonnet synthesize.

    :param candidates: Merged candidates with ``source_paths``.
    :return: Kept rows, rejected rows, and cluster hints for D1.
    """
    logger.info("prefilter_candidates | entry input_count=%s", len(candidates))
    kept: list[dict] = []
    rejected: list[dict] = []
    clusters: dict[str, list[str]] = {}

    for candidate in candidates:
        name = str(candidate.get("name") or "").strip()
        if not name:
            continue
        paths = list(candidate.get("source_paths") or [])
        reason = ""
        if _only_noise_sources(paths):
            reason = "noise_source_only"
        elif _is_test_lib_noise(candidate):
            reason = "test_lib_from_deps_file"
        if reason:
            rejected.append({**candidate, "reject_reason": reason})
            logger.info(
                "prefilter_candidates | reject name=%s reason=%s sources=%s",
                name,
                reason,
                paths,
            )
            continue
        kept.append(candidate)
        key = _normalize_cluster_key(name)
        clusters.setdefault(key, [])
        if name not in clusters[key]:
            clusters[key].append(name)

    logger.info(
        "prefilter_candidates | result kept=%s rejected=%s cluster_count=%s",
        len(kept),
        len(rejected),
        len(clusters),
    )
    return PrefilterResult(kept=kept, rejected=rejected, cluster_hints=clusters)
