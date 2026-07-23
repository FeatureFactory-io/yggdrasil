"""Munin bootstrap relationship planner — enriches Ratatosk element ops."""

from __future__ import annotations

import logging

from django.utils.text import slugify

from yggdrasil.changeset.models import ChangeSetItem

logger = logging.getLogger("yggdrasil.munin.bootstrap_planner")

# sample_webapp topology: component/application → container/technology
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
) -> tuple[list[dict], str]:
    """
    Append relationship ops to Ratatosk element-only bootstrap operations.

    :param model_id: YggdrasilModel PK.
    :param element_ops: Proposed element operations from Ratatosk.
    :param user_id: Requesting user PK (audit).
    :return: (merged operations, munin_reasoning summary).
    """
    logger.info(
        "MuninBootstrapPlanner.plan | model_id=%s element_ops=%s user_id=%s",
        model_id,
        len(element_ops),
        user_id,
    )
    names = _element_names_from_ops(element_ops)
    rel_ops = _infer_relationship_ops(names)
    merged = list(element_ops) + rel_ops
    add_el = sum(1 for op in element_ops if op.get("op_type") == ChangeSetItem.OP_ADD_ELEMENT)
    add_rel = len(rel_ops)
    summary = f"Bootstrap handoff: {add_el} add-element ops, {add_rel} add-relationship ops"
    logger.info(
        "MuninBootstrapPlanner.plan | relationship_ops=%s summary=%s",
        add_rel,
        summary,
    )
    return merged, summary


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
    """Rule-based relationship inference for bootstrap manifest."""
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
