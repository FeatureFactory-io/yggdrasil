"""Token-budget ModelSummary builder for Ratatosk CLI (SAO A5)."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

logger = logging.getLogger("ratatosk.discovery.model_summary")

DEFAULT_BUDGET_TOKENS = 8000
_CHARS_PER_TOKEN = 4


def build_model_summary(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
) -> tuple[str, dict[str, Any]]:
    """
    Build depth-expanded ModelSummary text under a token budget.

    :param elements: Element dicts from MCP list_elements (name, package, stereotype).
    :param relationships: Relationship dicts (optional).
    :param budget_tokens: Max token budget (chars proxy = budget * 4).
    :return: (summary_text, metadata for blackboard).
    """
    rels = relationships or []
    budget_chars = budget_tokens * _CHARS_PER_TOKEN
    logger.info(
        "build_model_summary | budget_tokens=%s elements=%s relationships=%s",
        budget_tokens,
        len(elements),
        len(rels),
    )
    lines: list[str] = []
    meta: dict[str, Any] = {
        "budget_tokens": budget_tokens,
        "depth_reached": "L0",
        "budget_exhausted": False,
    }

    l0 = f"L0 totals: {len(elements)} elements, {len(rels)} relationships."
    lines.append(l0)
    used = len(l0)

    if not elements:
        text = "\n".join(lines)
        meta["model_summary_chars"] = len(text)
        meta["depth_reached"] = "L0"
        logger.info("build_model_summary | chars=%s depth=L0 empty_model", len(text))
        return text, meta

    pkg_counts: Counter[str] = Counter()
    for el in elements:
        pkg = str(el.get("package") or el.get("package__name") or "unknown")
        pkg_counts[pkg] += 1
    l1_parts = [f"{pkg}: {count}" for pkg, count in sorted(pkg_counts.items())]
    l1 = "L1 packages: " + ", ".join(l1_parts)
    if used + len(l1) + 1 <= budget_chars:
        lines.append(l1)
        used += len(l1) + 1
        meta["depth_reached"] = "L1"

    names = sorted(str(el.get("name") or "") for el in elements if el.get("name"))
    l2 = "L2 elements: " + ", ".join(names)
    if used + len(l2) + 1 <= budget_chars:
        lines.append(l2)
        used += len(l2) + 1
        meta["depth_reached"] = "L2"
    else:
        meta["budget_exhausted"] = True

    text = "\n".join(lines)
    meta["model_summary_chars"] = len(text)
    meta["budget_remaining"] = max(0, budget_chars - len(text))
    logger.info(
        "build_model_summary | chars=%s depth=%s exhausted=%s",
        len(text),
        meta["depth_reached"],
        meta["budget_exhausted"],
    )
    return text, meta
