"""Unit tests for ratatosk.discovery.limits."""

from __future__ import annotations

from ratatosk.discovery.limits import (
    DEFAULT_MAX_EXTRACT_TARGETS,
    DiscoveryLimits,
    SAO_ARCHITECTURE_SOURCE,
    cap_extract_targets,
    prioritize_targets,
)


def test_prioritize_targets_puts_sao_after_readme() -> None:
    """SAO.md is second when both architecture docs are in tree."""
    tree = [
        "src/a.py",
        SAO_ARCHITECTURE_SOURCE,
        "README.md",
    ]
    targets = ["src/a.py"]
    ordered = prioritize_targets(tree, targets)
    assert ordered[0] == "README.md"
    assert ordered[1] == SAO_ARCHITECTURE_SOURCE


def test_cap_extract_targets_respects_effective_cap() -> None:
    """80 planner targets with cap 50 yields exactly 50."""
    limits = DiscoveryLimits(max_extract_targets=50, max_file_reads_per_run=1000)
    targets = [f"src/file_{index}.py" for index in range(80)]
    capped = cap_extract_targets(targets, limits)
    assert len(capped) == 50


def test_cap_extract_targets_uses_min_of_both_limits() -> None:
    """File read hard stop can be lower than extract target ceiling."""
    limits = DiscoveryLimits(max_extract_targets=100, max_file_reads_per_run=30)
    targets = [f"src/file_{index}.py" for index in range(100)]
    capped = cap_extract_targets(targets, limits)
    assert len(capped) == 30


def test_prioritize_targets_applies_default_cap() -> None:
    """Default limits cap at 50 even when tree is large."""
    tree = ["README.md"] + [f"src/file_{index}.py" for index in range(100)]
    targets = tree[1:]
    ordered = prioritize_targets(tree, targets)
    assert len(ordered) == DEFAULT_MAX_EXTRACT_TARGETS
