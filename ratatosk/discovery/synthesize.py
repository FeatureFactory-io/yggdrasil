"""Phase D1 Sonnet synthesize + D2 apply for bootstrap candidates."""

from __future__ import annotations

import json
import logging
from typing import Any

from yggdrasil.llm.structured import extract_json_object as _parse_json_object

logger = logging.getLogger("ratatosk.discovery.synthesize")


def apply_synthesis(
    candidates: list[dict],
    synthesis: dict[str, Any],
) -> tuple[list[dict], dict[str, Any]]:
    """
    Apply Sonnet synthesis JSON to pre-filtered candidates.

    :param candidates: Pre-filtered candidate dicts.
    :param synthesis: Parsed synthesis object with canonical/merges/rejects.
    :return: Canonical candidate list and metadata for blackboard/handoff.
    """
    before = len(candidates)
    drop_names = {str(m.get("drop") or "") for m in (synthesis.get("merges") or [])}
    drop_names |= {str(r.get("name") or "") for r in (synthesis.get("rejects") or [])}
    drop_names.discard("")

    canonical_raw = synthesis.get("canonical")
    if isinstance(canonical_raw, list) and canonical_raw:
        canonical = [dict(item) for item in canonical_raw if item.get("name")]
    else:
        canonical = [c for c in candidates if str(c.get("name") or "") not in drop_names]

    merge_map = {
        str(m.get("drop") or ""): str(m.get("keep") or "")
        for m in (synthesis.get("merges") or [])
        if m.get("drop") and m.get("keep")
    }
    do_not_reference = sorted(drop_names | set(merge_map.keys()))

    meta = {
        "before_count": before,
        "after_count": len(canonical),
        "merges": synthesis.get("merges") or [],
        "rejects": synthesis.get("rejects") or [],
        "merge_map": merge_map,
        "do_not_reference": do_not_reference,
        "notes": str(synthesis.get("notes") or ""),
        "canonical_count": len(canonical),
    }
    logger.info(
        "apply_synthesis | before=%s after=%s merges=%s rejects=%s do_not_reference=%s",
        before,
        len(canonical),
        len(meta["merges"]),
        len(meta["rejects"]),
        len(do_not_reference),
    )
    return canonical, meta


def _llm_synthesize_candidates(
    planning_llm: Any,
    candidates: list[dict],
    ontology: str,
    cluster_hints: dict[str, list[str]],
    instructions: str = "",
) -> dict[str, Any]:
    """
    One Sonnet batch call to canonicalize duplicate/noisy bootstrap candidates.

    :param planning_llm: Planning-tier LLM client.
    :param candidates: Pre-filtered candidates with source_paths.
    :param ontology: Metamodel guidance text.
    :param cluster_hints: Normalized name clusters from D0.
    :param instructions: Optional operator instructions.
    :return: Parsed synthesis dict (may be empty on failure).
    """
    from ratatosk.discovery.scripted_llm import LLMMessage

    logger.info(
        "_llm_synthesize_candidates | entry count=%s clusters=%s llm=%s",
        len(candidates),
        len(cluster_hints),
        getattr(planning_llm, "model_id", type(planning_llm).__name__),
    )
    payload = [
        {
            "name": c.get("name"),
            "stereotype": c.get("stereotype"),
            "package": c.get("package"),
            "confidence": c.get("confidence"),
            "source_paths": c.get("source_paths") or [],
        }
        for c in candidates
    ]
    system = (
        "You are Ratatosk synthesizing bootstrap architecture candidates. "
        "Return JSON only. Merge synonyms, reject noise, keep SAO/README canonical names."
    )
    user_content = (
        "Given these bootstrap element candidates, return ONLY JSON:\n"
        '{"canonical": [...], "merges": [{"drop","keep","reason"}], '
        '"rejects": [{"name","reason"}], "notes": "..."}\n'
        "Rules:\n"
        "- Prefer names from docs/architecture/SAO.md and README when merging duplicates\n"
        "- Reject fixture/test/UI noise (sample_webapp names, screen IDs, test libraries)\n"
        "- Do not invent new elements; only canonicalize from input list\n"
        "- Each canonical entry keeps best confidence and union of source_paths\n\n"
        f"Cluster hints (possible duplicates): {json.dumps(cluster_hints)}\n"
        f"Instructions: {instructions[:500] or '(none)'}\n\n"
        f"{ontology}\n\n"
        f"Candidates ({len(payload)}):\n{json.dumps(payload)[:12000]}"
    )
    response = planning_llm.complete(
        messages=[LLMMessage(role="user", content=user_content)],
        system=system,
    ).content
    parsed = _parse_json_object(response) or {}
    if not parsed:
        logger.warning(
            "_llm_synthesize_candidates | branch=fallback reason=empty_or_invalid_json",
        )
        return {}
    logger.info(
        "_llm_synthesize_candidates | branch=llm canonical=%s merges=%s rejects=%s",
        len(parsed.get("canonical") or []),
        len(parsed.get("merges") or []),
        len(parsed.get("rejects") or []),
    )
    return parsed


def run_synthesis_phase(
    planning_llm: Any,
    candidates: list[dict],
    ontology: str,
    cluster_hints: dict[str, list[str]],
    instructions: str = "",
) -> tuple[list[dict], dict[str, Any]]:
    """
    Run D1 synthesize and D2 apply with fail-open fallback.

    :return: (canonical_candidates, synthesis_meta)
    """
    synthesis = _llm_synthesize_candidates(
        planning_llm,
        candidates,
        ontology,
        cluster_hints,
        instructions,
    )
    if not synthesis:
        meta = {
            "before_count": len(candidates),
            "after_count": len(candidates),
            "merges": [],
            "rejects": [],
            "merge_map": {},
            "do_not_reference": [],
            "notes": "synthesis_fallback_pass_through",
            "canonical_count": len(candidates),
            "fallback": True,
        }
        logger.info("run_synthesis_phase | fallback pass_through count=%s", len(candidates))
        return candidates, meta
    return apply_synthesis(candidates, synthesis)
