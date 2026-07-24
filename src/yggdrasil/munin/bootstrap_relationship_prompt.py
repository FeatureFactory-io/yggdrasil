"""Munin bootstrap relationship planning prompts (metamodel-native)."""

from __future__ import annotations

import json
import os
from typing import Any

from yggdrasil.graph.metamodel_guidance import build_metamodel_guidance

DEFAULT_MAX_INBOUND_DEPENDS = 8
_SYSTEM_PROMPT = (
    "You are Munin, the Yggdrasil ontology planner. "
    "Plan relationship edges for bootstrap element candidates. Return valid JSON only."
)


def _max_inbound_depends() -> int:
    raw = os.environ.get("MUNIN_MAX_INBOUND_DEPENDS", str(DEFAULT_MAX_INBOUND_DEPENDS))
    try:
        return max(1, int(raw))
    except (TypeError, ValueError):
        return DEFAULT_MAX_INBOUND_DEPENDS


def _group_elements_by_tier(elements: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    tiers: dict[str, list[dict[str, str]]] = {
        "systems": [],
        "containers": [],
        "components": [],
        "other": [],
    }
    for item in elements:
        st = str(item.get("stereotype_slug") or "")
        if st == "system":
            tiers["systems"].append(item)
        elif st == "container":
            tiers["containers"].append(item)
        elif st == "component":
            tiers["components"].append(item)
        else:
            tiers["other"].append(item)
    return tiers


def build_relationship_plan_prompt(
    metamodel: Any,
    elements: list[dict[str, str]],
    handoff_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Build system and user prompts for Munin bootstrap relationship planning.

    :param metamodel: Bound ``Metamodel`` ORM instance.
    :param elements: Element metadata from element ops.
    :param handoff_context: Optional Ratatosk handoff (synthesize, instructions).
    :return: (system_prompt, user_prompt)
    """
    ctx = handoff_context or {}
    synth = ctx.get("synthesize") or {}
    do_not_reference = list(synth.get("do_not_reference") or [])
    instructions = str(ctx.get("instructions") or "").strip()
    tiers = _group_elements_by_tier(elements)
    max_inbound = _max_inbound_depends()

    planning_rules = (
        "## Planning rules (metamodel-generic)\n"
        "- Respect allowed_edge_rules for each source element stereotype\n"
        "- Components should depends_on their hosting container(s)\n"
        "- Infra containers (technology package, datastores, queues) are dependency targets\n"
        f"- Avoid hub topology: non-infra targets should have at most {max_inbound} inbound depends_on\n"
        "- Use only element names from the canonical lists below\n"
        "- Use only relationship stereotype slugs from the metamodel\n"
    )
    if do_not_reference:
        planning_rules += f"- Do NOT reference these dropped/merged names: {do_not_reference}\n"
    if instructions:
        planning_rules += f"\n## Operator instructions\n{instructions[:800]}\n"

    user = (
        f"{build_metamodel_guidance(metamodel)}\n\n"
        f"{planning_rules}\n"
        "## Canonical elements by tier\n"
        f"systems: {json.dumps(tiers['systems'])}\n"
        f"containers: {json.dumps(tiers['containers'])}\n"
        f"components: {json.dumps(tiers['components'])}\n"
        f"other: {json.dumps(tiers['other'])}\n\n"
        "Return ONLY JSON:\n"
        '{"strategy": "one paragraph", "relationships": ['
        '{"source_name","target_name","stereotype_slug","confidence","rationale"}]}\n'
    )
    return _SYSTEM_PROMPT, user


def build_structure_plan_prompt(
    metamodel: Any,
    elements: list[dict[str, str]],
    handoff_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Prompt for Munin call 1: structural hierarchy edges only."""
    system, user = build_relationship_plan_prompt(metamodel, elements, handoff_context)
    user += (
        "\nFocus this pass on: system→container, component→container placement. "
        "Skip infra cross-cutting edges."
    )
    return system, user


def build_crosscutting_plan_prompt(
    metamodel: Any,
    elements: list[dict[str, str]],
    handoff_context: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Prompt for Munin call 2: infra and cross-container edges."""
    system, user = build_relationship_plan_prompt(metamodel, elements, handoff_context)
    user += (
        "\nFocus this pass on: infra dependencies, facade/CLI→backend, external uses/calls. "
        "Do not repeat component→container edges from structural pass."
    )
    return system, user


def estimate_prompt_tokens(text: str) -> int:
    """Rough token estimate (chars / 4) for split decision."""
    return max(1, len(text) // 4)


def should_split_relationship_planning(user_prompt: str, budget: int = 12_000) -> bool:
    """
    Decide whether to split Munin into two Sonnet calls.

    :param user_prompt: Full user prompt text.
    :param budget: Token budget threshold.
    :return: True when estimate exceeds budget.
    """
    return estimate_prompt_tokens(user_prompt) > budget
