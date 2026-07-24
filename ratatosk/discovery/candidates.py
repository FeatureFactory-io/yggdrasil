"""Candidate merge helpers with file provenance."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("ratatosk.discovery.candidates")


def attach_source_paths(candidates: list[dict], source_label: str) -> list[dict]:
    """
    Tag each candidate with the file path it was extracted from.

    :param candidates: Raw LLM extract rows.
    :param source_label: Relative path or stdin label.
    :return: Candidates with ``source_paths`` list populated.
    """
    if not source_label:
        return candidates
    tagged: list[dict] = []
    for raw in candidates:
        item = dict(raw)
        paths = list(item.get("source_paths") or [])
        if source_label not in paths:
            paths.append(source_label)
        item["source_paths"] = paths
        tagged.append(item)
    logger.info(
        "attach_source_paths | source=%s count=%s",
        source_label,
        len(tagged),
    )
    return tagged


def _slugify(name: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", name.strip().lower())
    return text.strip("-") or "unknown"


def merge_candidates_by_slug(candidates: list[dict]) -> list[dict]:
    """
    Merge candidates sharing the same name slug; union source_paths, keep max confidence.

    :param candidates: Tagged candidate dicts.
    :return: De-duplicated list by slug.
    """
    by_slug: dict[str, dict] = {}
    for raw in candidates:
        name = str(raw.get("name") or "").strip()
        if not name:
            continue
        slug = _slugify(name)
        conf = float(raw.get("confidence", 0))
        paths = list(raw.get("source_paths") or [])
        prior = by_slug.get(slug)
        if prior is None:
            by_slug[slug] = {**raw, "name": name, "source_paths": paths}
            continue
        merged_paths = list(dict.fromkeys([*(prior.get("source_paths") or []), *paths]))
        if conf > float(prior.get("confidence", 0)):
            by_slug[slug] = {**raw, "name": name, "source_paths": merged_paths}
        else:
            prior["source_paths"] = merged_paths
            by_slug[slug] = prior
    merged = list(by_slug.values())
    logger.info(
        "merge_candidates_by_slug | input=%s output=%s",
        len(candidates),
        len(merged),
    )
    return merged
