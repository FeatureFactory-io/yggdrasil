"""LLM-backed bootstrap relationship inference for Munin."""

from __future__ import annotations

import json
import logging
from typing import Any

from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.graph.models import YggdrasilModel
from yggdrasil.llm.base import LLMMessage
from yggdrasil.llm.structured import extract_json_object, normalize_llm_text
from yggdrasil.munin.bootstrap_relationship_prompt import (
    _max_inbound_depends,
    build_crosscutting_plan_prompt,
    build_relationship_plan_prompt,
    build_structure_plan_prompt,
    should_split_relationship_planning,
)
from yggdrasil.munin.logging_utils import (
    log_munin_branch,
    log_munin_entry,
    log_munin_error,
    log_munin_exit,
    log_munin_llm_request,
    log_munin_llm_response,
    log_munin_structure,
)

logger = logging.getLogger("yggdrasil.munin.bootstrap_relationship_llm")

_WHERE = "bootstrap_relationship_llm.infer_bootstrap_relationship_ops"
_EDGE_TYPES = ("depends_on", "uses", "communicates_with", "calls")


def infer_bootstrap_relationship_ops(
    *,
    element_ops: list[dict],
    llm: Any | None = None,
    user_id: int | None = None,
    model_id: int | None = None,
    handoff_context: dict[str, Any] | None = None,
) -> tuple[list[dict], str, str]:
    """
    Infer relationship operations from bootstrap element operations via LLM.

    :param element_ops: Ratatosk add/update element operations.
    :param llm: LLM client with ``complete`` method.
    :param user_id: Requesting user PK for audit logs.
    :param model_id: YggdrasilModel PK for metamodel guidance.
    :param handoff_context: Ratatosk synthesis/instructions context.
    :return: Tuple of (relationship ops, source tag, strategy text).
    """
    llm_model = getattr(llm, "model_id", type(llm).__name__) if llm is not None else "none"
    log_munin_entry(
        "infer_bootstrap_relationship_ops",
        where=_WHERE,
        user_id=user_id,
        llm_model=llm_model,
        element_op_count=len(element_ops),
        model_id=model_id,
    )

    elements = _elements_from_ops(element_ops)
    names = {item["name"] for item in elements}
    log_munin_structure("bootstrap_elements", elements)

    if not names or llm is None:
        reason = "missing_llm" if llm is None else "empty_element_ops"
        log_munin_branch(
            where=_WHERE,
            branch="skipped",
            reason=reason,
            user_id=user_id,
            element_count=len(names),
            llm_present=llm is not None,
        )
        log_munin_exit(
            "infer_bootstrap_relationship_ops",
            where=_WHERE,
            user_id=user_id,
            success=True,
            source="none",
            relationship_count=0,
        )
        return [], "none", ""

    metamodel = _load_metamodel(model_id)
    ctx = handoff_context or {}
    do_not_reference = set(ctx.get("synthesize", {}).get("do_not_reference") or [])

    system, user_prompt = build_relationship_plan_prompt(metamodel, elements, ctx)
    log_munin_branch(
        where=_WHERE,
        branch="build_relationship_plan_prompt",
        reason="metamodel_guidance_prompt_built",
        metamodel_slug=metamodel.slug,
        tier_systems=sum(1 for e in elements if e.get("stereotype_slug") == "system"),
        tier_containers=sum(1 for e in elements if e.get("stereotype_slug") == "container"),
        tier_components=sum(1 for e in elements if e.get("stereotype_slug") == "component"),
        do_not_reference_count=len(do_not_reference),
    )

    if should_split_relationship_planning(user_prompt):
        log_munin_branch(where=_WHERE, branch="split_two_call", reason="token_budget_exceeded")
        rels, strategy = _infer_split_calls(llm, metamodel, elements, ctx, user_id, llm_model)
    else:
        rels, strategy = _infer_single_call(
            llm, system, user_prompt, user_id, llm_model, names, do_not_reference, elements
        )

    ops, rejected = _ops_from_llm_payload(
        rels,
        names,
        do_not_reference=do_not_reference,
        elements=elements,
        user_id=user_id,
    )
    ops = _apply_anti_star(ops, elements)
    source = "llm" if ops else "none"

    log_munin_llm_response(
        where=_WHERE,
        user_id=user_id,
        llm_model=llm_model,
        raw_content=strategy,
        parsed_count=len(rels),
        accepted_count=len(ops),
        rejected_count=rejected,
    )
    log_munin_structure("accepted_relationship_ops", ops)
    log_munin_exit(
        "infer_bootstrap_relationship_ops",
        where=_WHERE,
        user_id=user_id,
        success=bool(ops),
        source=source,
        relationship_count=len(ops),
        strategy_chars=len(strategy),
    )
    return ops, source, strategy


def _load_metamodel(model_id: int | None) -> Any:
    if model_id is None:
        from yggdrasil.graph.models import ensure_c4_metamodel

        return ensure_c4_metamodel()
    ymodel = YggdrasilModel.objects.select_related("metamodel").get(pk=model_id)
    return ymodel.metamodel


def _infer_single_call(
    llm: Any,
    system: str,
    user_prompt: str,
    user_id: int | None,
    llm_model: str,
    names: set[str],
    do_not_reference: set[str],
    elements: list[dict[str, str]],
) -> tuple[list[dict], str]:
    log_munin_llm_request(
        where=_WHERE,
        user_id=user_id,
        llm_model=llm_model,
        system=system,
        prompt=user_prompt,
        element_count=len(names),
    )
    try:
        response = llm.complete(
            messages=[LLMMessage(role="user", content=user_prompt)],
            system=system,
        )
    except Exception as exc:
        log_munin_error(
            "infer_bootstrap_relationship_ops",
            where=_WHERE,
            error=exc,
            user_id=user_id,
            llm_model=llm_model,
        )
        return [], ""
    return _parse_plan_response(response.content or "")


def _infer_split_calls(
    llm: Any,
    metamodel: Any,
    elements: list[dict[str, str]],
    ctx: dict[str, Any],
    user_id: int | None,
    llm_model: str,
) -> tuple[list[dict], str]:
    strategies: list[str] = []
    all_rels: list[dict] = []
    for label, builder in (
        ("structure", build_structure_plan_prompt),
        ("crosscutting", build_crosscutting_plan_prompt),
    ):
        system, prompt = builder(metamodel, elements, ctx)
        log_munin_llm_request(
            where=_WHERE,
            user_id=user_id,
            llm_model=llm_model,
            system=system,
            prompt=prompt,
            element_count=len(elements),
            split_pass=label,
        )
        try:
            response = llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system=system,
            )
        except Exception as exc:
            log_munin_error(
                "infer_bootstrap_relationship_ops",
                where=_WHERE,
                error=exc,
                user_id=user_id,
                split_pass=label,
            )
            continue
        rels, strategy = _parse_plan_response(response.content or "")
        strategies.append(strategy)
        all_rels.extend(rels)
    deduped = _dedupe_relationships(all_rels)
    return deduped, " | ".join(s for s in strategies if s)


def _parse_plan_response(raw: str) -> tuple[list[dict], str]:
    text = normalize_llm_text(raw)
    obj = extract_json_object(text) if text else {}
    if isinstance(obj, dict) and obj.get("relationships") is not None:
        strategy = str(obj.get("strategy") or "")
        rels = obj.get("relationships") or []
        if isinstance(rels, list):
            return [r for r in rels if isinstance(r, dict)], strategy
    return _parse_relationship_array(raw), ""


def _dedupe_relationships(rels: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for item in rels:
        key = (
            str(item.get("source_name") or ""),
            str(item.get("target_name") or ""),
            str(item.get("stereotype_slug") or "depends_on"),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _apply_anti_star(ops: list[dict], elements: list[dict[str, str]]) -> list[dict]:
    """Cap inbound depends_on per non-infra target."""
    max_inbound = _max_inbound_depends()
    infra_names = {
        e["name"]
        for e in elements
        if e.get("stereotype_slug") == "container"
        and e.get("package_slug") == "technology"
        and any(
            tok in e["name"].lower() for tok in ("postgres", "redis", "database", "queue", "ollama")
        )
    }
    inbound: dict[str, int] = {}
    kept: list[dict] = []
    dropped = 0
    for op in ops:
        detail = op.get("detail") or {}
        target = str(detail.get("target_name") or "")
        edge = str(detail.get("stereotype_slug") or "")
        if edge != "depends_on" or target in infra_names:
            kept.append(op)
            continue
        count = inbound.get(target, 0)
        if count >= max_inbound:
            dropped += 1
            continue
        inbound[target] = count + 1
        kept.append(op)
    if dropped:
        logger.info(
            "infer_bootstrap_relationship_ops | anti_star dropped_hub_edges=%s max_inbound=%s",
            dropped,
            max_inbound,
        )
    return kept


def _elements_from_ops(ops: list[dict]) -> list[dict[str, str]]:
    """Collect element metadata from add/update element operations."""
    elements: list[dict[str, str]] = []
    seen: set[str] = set()
    for op in ops:
        if op.get("op_type") not in {
            ChangeSetItem.OP_ADD_ELEMENT,
            ChangeSetItem.OP_UPDATE_ELEMENT,
        }:
            continue
        detail = op.get("detail") or {}
        name = str(detail.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        elements.append(
            {
                "name": name,
                "stereotype_slug": str(detail.get("stereotype_slug") or ""),
                "package_slug": str(detail.get("package_slug") or ""),
            }
        )
    return sorted(elements, key=lambda item: item["name"])


def _parse_relationship_array(raw: str) -> list[dict]:
    """Parse relationship JSON array (legacy shape)."""
    text = normalize_llm_text(raw)
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end <= start:
            return []
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return []
    if isinstance(data, dict) and "relationships" in data:
        data = data["relationships"]
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _ops_from_llm_payload(
    payload: list[Any],
    allowed_names: set[str],
    *,
    do_not_reference: set[str],
    elements: list[dict[str, str]],
    user_id: int | None = None,
) -> tuple[list[dict], int]:
    """Convert LLM JSON array into add-relationship ChangeSet ops."""
    ops: list[dict] = []
    rejected = 0
    for item in payload:
        if not isinstance(item, dict):
            rejected += 1
            continue
        source_name = str(item.get("source_name") or "").strip()
        target_name = str(item.get("target_name") or "").strip()
        if source_name in do_not_reference or target_name in do_not_reference:
            rejected += 1
            logger.info(
                "_ops_from_llm_payload | rejected user_id=%s reason=do_not_reference "
                "source=%s target=%s",
                user_id,
                source_name,
                target_name,
            )
            continue
        if not source_name or not target_name:
            rejected += 1
            continue
        if source_name not in allowed_names or target_name not in allowed_names:
            rejected += 1
            continue
        edge_slug = str(item.get("stereotype_slug") or "depends_on").strip().lower()
        if edge_slug not in _EDGE_TYPES:
            edge_slug = "depends_on"
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": source_name,
                    "target_name": target_name,
                    "source_slug": slugify(source_name),
                    "target_slug": slugify(target_name),
                    "stereotype_slug": edge_slug,
                },
                "confidence": float(item.get("confidence") or 0.82),
            }
        )
    return ops, rejected
