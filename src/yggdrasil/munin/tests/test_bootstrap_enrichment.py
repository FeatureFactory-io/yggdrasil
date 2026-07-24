"""Tests for Munin metamodel-native bootstrap relationship planning."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.munin.bootstrap_relationship_llm import (
    _apply_anti_star,
    _ops_from_llm_payload,
    _parse_plan_response,
    infer_bootstrap_relationship_ops,
)
from yggdrasil.munin.bootstrap_relationship_prompt import (
    build_relationship_plan_prompt,
    should_split_relationship_planning,
)


def test_munin_prompt_includes_metamodel_guidance(db) -> None:
    """Prompt contains stereotype slug and allowed_edge_rules from catalog."""
    mm = ensure_c4_metamodel()
    elements = [
        {"name": "Order Service", "stereotype_slug": "container", "package_slug": "technology"},
        {"name": "Order Domain", "stereotype_slug": "component", "package_slug": "application"},
    ]
    _system, user = build_relationship_plan_prompt(mm, elements, {})
    assert "allowed_edge_rules" in user
    assert "### `container`" in user
    assert "depends_on" in user


def test_munin_rejects_edges_to_do_not_reference_names() -> None:
    """Edges referencing merged-away names are dropped."""
    payload = [
        {
            "source_name": "Order Domain",
            "target_name": "Backend",
            "stereotype_slug": "depends_on",
            "confidence": 0.9,
        }
    ]
    ops, rejected = _ops_from_llm_payload(
        payload,
        {"Order Domain", "Order Service"},
        do_not_reference={"Backend"},
        elements=[
            {"name": "Order Domain", "stereotype_slug": "component", "package_slug": "application"}
        ],
    )
    assert ops == []
    assert rejected == 1


def test_munin_anti_star_caps_inbound_depends_on() -> None:
    """Ninth inbound depends_on to a non-infra target is dropped."""
    elements = [
        {"name": "Hub", "stereotype_slug": "container", "package_slug": "application"},
    ]
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
            "detail": {
                "source_name": f"Source {index}",
                "target_name": "Hub",
                "stereotype_slug": "depends_on",
            },
            "confidence": 0.9,
        }
        for index in range(10)
    ]
    capped = _apply_anti_star(ops, elements)
    assert len(capped) == 8


def test_munin_parses_strategy_and_relationships_json() -> None:
    """Strategy text and relationships array are parsed from Munin JSON."""
    raw = json.dumps(
        {
            "strategy": "Place components under containers; wire infra last.",
            "relationships": [
                {
                    "source_name": "A",
                    "target_name": "B",
                    "stereotype_slug": "depends_on",
                    "confidence": 0.9,
                }
            ],
        }
    )
    rels, strategy = _parse_plan_response(raw)
    assert strategy.startswith("Place components")
    assert len(rels) == 1


def test_should_split_relationship_planning_when_over_budget() -> None:
    """Two-call split triggers when prompt exceeds token budget."""
    huge = "x" * 50_000
    assert should_split_relationship_planning(huge, budget=12_000) is True
    assert should_split_relationship_planning("small prompt", budget=12_000) is False


class _StrategyLLM:
    model_id = "fake-munin-strategy"

    def complete(self, messages, system="", max_tokens=1024, temperature=0.2):
        from yggdrasil.llm.base import LLMResponse

        payload = {
            "strategy": "Components depend on their hosting containers.",
            "relationships": [
                {
                    "source_name": "Service A",
                    "target_name": "Service B",
                    "stereotype_slug": "depends_on",
                    "confidence": 0.9,
                }
            ],
        }
        return LLMResponse(content=json.dumps(payload), model=self.model_id)


def test_infer_bootstrap_relationship_ops_returns_strategy(db) -> None:
    """infer returns strategy text for blackboard / munin_reasoning."""
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": "Service A",
                "stereotype_slug": "component",
                "package_slug": "application",
            },
            "confidence": 0.95,
        },
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": "Service B",
                "stereotype_slug": "container",
                "package_slug": "technology",
            },
            "confidence": 0.95,
        },
    ]
    rel_ops, source, strategy = infer_bootstrap_relationship_ops(
        element_ops=ops,
        llm=_StrategyLLM(),
        handoff_context={"synthesize": {"do_not_reference": []}},
    )
    assert source == "llm"
    assert rel_ops
    assert "Components depend" in strategy


@pytest.mark.django_db
def test_propose_changeset_passes_handoff_context_to_planner(rw_user) -> None:
    """Integration: propose_changeset forwards synthesis context to Munin planner."""
    from tests.fixtures.factories.model_factories import YggdrasilModelFactory

    from yggdrasil.mcp.tools.propose import propose_changeset

    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    handoff = {
        "synthesize": {
            "merges": [{"drop": "Backend", "keep": "Backend container", "reason": "dup"}],
            "rejects": [],
            "do_not_reference": ["Backend"],
            "canonical_count": 2,
        },
        "instructions": "focus on SAO",
        "metamodel_slug": "c4",
    }
    captured: dict = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        element_ops = list(kwargs.get("element_ops") or [])
        return element_ops, "mock summary"

    with patch(
        "yggdrasil.munin.bootstrap_planner.plan_bootstrap_changeset",
        side_effect=_capture,
    ) as mock_plan:
        propose_changeset(
            model="yggdrasil",
            operations=[
                {
                    "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                    "detail": {
                        "name": "Service A",
                        "stereotype_slug": "component",
                        "package_slug": "application",
                    },
                    "confidence": 0.95,
                }
            ],
            source="ratatosk",
            run_id="run-handoff-ctx",
            handoff_context=handoff,
        )
    assert mock_plan.called
    assert captured.get("handoff_context") == handoff


@pytest.fixture
def rw_user(db):
    from tests.fixtures.factories import UserFactory

    from yggdrasil.mcp.server import set_current_user_id, set_token_scope

    user = UserFactory(username="munin-enrichment", is_architect=True)
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    yield user
    set_current_user_id(None)
    set_token_scope("read-write")
