"""Munin bootstrap relationship planner — enriches Ratatosk element ops."""

from __future__ import annotations

import logging
import os
from typing import Any

from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.munin.bootstrap_relationship_llm import infer_bootstrap_relationship_ops
from yggdrasil.munin.llm_factory import munin_allows_manifest_fallback
from yggdrasil.munin.logging_utils import (
    log_munin_branch,
    log_munin_entry,
    log_munin_exit,
    log_munin_structure,
)

logger = logging.getLogger("yggdrasil.munin.bootstrap_planner")

_WHERE = "bootstrap_planner.plan_bootstrap_changeset"

# sample_webapp topology — scripted AT fallback only
_BOOTSTRAP_EDGES: list[tuple[str, str, str]] = [
    ("Order Domain", "Order Service", "depends_on"),
    ("Billing Worker", "Order Domain", "depends_on"),
    ("Order Service", "Payment API", "depends_on"),
]


def plan_bootstrap_changeset(
    *,
    model_id: int,
    element_ops: list[dict],
    user_id: int | None = None,
    llm: Any | None = None,
    confidence_threshold: float = 0.80,
    handoff_context: dict[str, Any] | None = None,
) -> tuple[list[dict], str]:
    """
    Append relationship ops to Ratatosk element-only bootstrap operations.

    :param model_id: YggdrasilModel PK.
    :param element_ops: Proposed element operations from Ratatosk.
    :param user_id: Requesting user PK (audit).
    :param llm: Munin planning-tier LLM client.
    :param confidence_threshold: Only plan edges between elements at/above this confidence.
    :return: (merged operations, munin_reasoning summary).
    """
    llm_model = getattr(llm, "model_id", "none") if llm is not None else "none"
    applied_names = _applied_element_names(element_ops, confidence_threshold)
    log_munin_entry(
        "plan_bootstrap_changeset",
        where=_WHERE,
        user_id=user_id,
        model_id=model_id,
        llm_model=llm_model,
        element_op_count=len(element_ops),
        applied_element_count=len(applied_names),
        confidence_threshold=confidence_threshold,
        why="ratatosk_element_only_handoff_requires_relationship_planning",
    )
    log_munin_structure("incoming_element_ops", element_ops)

    names = _element_names_from_ops(element_ops)
    log_munin_structure("element_names", sorted(names))
    log_munin_structure("applied_element_names", sorted(applied_names))

    eligible_ops = _element_ops_for_munin(element_ops, applied_names)
    log_munin_branch(
        where=_WHERE,
        branch="munin_element_scope",
        reason="only_auto_applied_elements_used_for_relationship_inference",
        user_id=user_id,
        total_elements=len(names),
        applied_elements=len(applied_names),
        excluded_elements=sorted(names - applied_names),
    )

    llm_ops, llm_source, strategy = infer_bootstrap_relationship_ops(
        element_ops=eligible_ops,
        llm=llm,
        user_id=user_id,
        model_id=model_id,
        handoff_context=handoff_context,
    )
    llm_ops = _filter_relationship_ops_for_applied_elements(llm_ops, applied_names)
    if llm_ops:
        rel_ops = llm_ops
        source = llm_source
        log_munin_branch(
            where=_WHERE,
            branch="llm_inferred",
            reason="infer_bootstrap_relationship_ops_returned_ops",
            user_id=user_id,
            relationship_count=len(rel_ops),
            source=source,
        )
    elif llm is not None and munin_allows_manifest_fallback(llm):
        rel_ops = _infer_relationship_ops(names)
        source = "manifest_scripted" if rel_ops else "none"
        log_munin_branch(
            where=_WHERE,
            branch="manifest_scripted_fallback",
            reason="scripted_munin_llm_and_llm_returned_zero",
            user_id=user_id,
            relationship_count=len(rel_ops),
            source=source,
        )
    else:
        rel_ops = []
        source = "none"
        log_munin_branch(
            where=_WHERE,
            branch="no_relationships",
            reason="real_llm_returned_zero_and_manifest_fallback_disabled",
            user_id=user_id,
            llm_model=llm_model,
            element_count=len(names),
        )
        if names and llm is not None and _require_relationships_enabled():
            msg = (
                "Munin bootstrap produced zero relationship ops with a real LLM provider; "
                f"element_names={sorted(names)}"
            )
            logger.error(
                "MuninBootstrapPlanner.plan | hard_fail user_id=%s reason=%s", user_id, msg
            )
            raise RuntimeError(msg)

    log_munin_structure("relationship_ops", rel_ops)

    merged = list(element_ops) + rel_ops
    add_el = sum(1 for op in element_ops if op.get("op_type") == ChangeSetItem.OP_ADD_ELEMENT)
    add_rel = len(rel_ops)
    summary = (
        f"Bootstrap handoff: {add_el} add-element ops, {add_rel} add-relationship ops "
        f"(source={source})"
    )
    if strategy:
        summary = f"{summary}; strategy={strategy[:200]}"
    log_munin_exit(
        "plan_bootstrap_changeset",
        where=_WHERE,
        user_id=user_id,
        success=add_rel > 0,
        source=source,
        add_element_ops=add_el,
        add_relationship_ops=add_rel,
        total_ops=len(merged),
        summary=summary,
    )
    return merged, summary


def _require_relationships_enabled() -> bool:
    """True when ``MUNIN_BOOTSTRAP_REQUIRE_RELATIONSHIPS=1``."""
    return str(os.environ.get("MUNIN_BOOTSTRAP_REQUIRE_RELATIONSHIPS") or "").strip() == "1"


def _applied_element_names(ops: list[dict], confidence_threshold: float) -> set[str]:
    """Element names from ops that will be auto-applied at the given threshold."""
    names: set[str] = set()
    for op in ops:
        if op.get("op_type") not in {
            ChangeSetItem.OP_ADD_ELEMENT,
            ChangeSetItem.OP_UPDATE_ELEMENT,
        }:
            continue
        if float(op.get("confidence") or 0) < confidence_threshold:
            continue
        detail = op.get("detail") or {}
        name = detail.get("name")
        if name:
            names.add(str(name))
    return names


def _element_ops_for_munin(ops: list[dict], applied_names: set[str]) -> list[dict]:
    """Subset of element ops Munin may use for relationship inference."""
    eligible: list[dict] = []
    for op in ops:
        if op.get("op_type") not in {
            ChangeSetItem.OP_ADD_ELEMENT,
            ChangeSetItem.OP_UPDATE_ELEMENT,
        }:
            continue
        detail = op.get("detail") or {}
        name = str(detail.get("name") or "").strip()
        if name and name in applied_names:
            eligible.append(op)
    return eligible


def _filter_relationship_ops_for_applied_elements(
    rel_ops: list[dict],
    applied_names: set[str],
) -> list[dict]:
    """Drop relationship ops whose endpoints are not in the applied element set."""
    kept: list[dict] = []
    for op in rel_ops:
        detail = op.get("detail") or {}
        source = str(detail.get("source_name") or "").strip()
        target = str(detail.get("target_name") or "").strip()
        if source in applied_names and target in applied_names:
            kept.append(op)
        else:
            logger.info(
                "plan_bootstrap_changeset | drop_relationship source=%s target=%s "
                "reason=endpoint_below_confidence_threshold",
                source,
                target,
            )
    return kept


def _element_names_from_ops(ops: list[dict]) -> set[str]:
    """Collect element names from add/update element operations."""
    names: set[str] = set()
    for op in ops:
        if op.get("op_type") not in {
            ChangeSetItem.OP_ADD_ELEMENT,
            ChangeSetItem.OP_UPDATE_ELEMENT,
        }:
            continue
        detail = op.get("detail") or {}
        name = detail.get("name")
        if name:
            names.add(str(name))
    return names


def _infer_relationship_ops(names: set[str]) -> list[dict]:
    """Rule-based relationship inference for scripted bootstrap manifest."""
    ops: list[dict] = []
    for source_name, target_name, edge_slug in _BOOTSTRAP_EDGES:
        if source_name in names and target_name in names:
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
                    "confidence": 0.85,
                }
            )
    return ops


def should_enrich_ratatosk_ops(source: str, operations: list[dict]) -> bool:
    """True when Munin should append relationship ops for Ratatosk bootstrap."""
    if source != "ratatosk":
        return False
    has_element = any(
        op.get("op_type")
        in {
            ChangeSetItem.OP_ADD_ELEMENT,
            ChangeSetItem.OP_UPDATE_ELEMENT,
        }
        for op in operations
    )
    has_relationship = any(
        op.get("op_type")
        in {
            ChangeSetItem.OP_ADD_RELATIONSHIP,
            ChangeSetItem.OP_DELETE_RELATIONSHIP,
        }
        for op in operations
    )
    return has_element and not has_relationship
