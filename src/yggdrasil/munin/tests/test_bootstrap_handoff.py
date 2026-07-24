"""Tests for Munin bootstrap handoff (ACT-1-CLI-04)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, Relationship, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset
from yggdrasil.munin.bootstrap_planner import plan_bootstrap_changeset, should_enrich_ratatosk_ops
from yggdrasil.munin.llm_factory import ScriptedMuninLLM, build_munin_planning_llm


@pytest.fixture
def rw_user(db):
    user = UserFactory(username="munin-bootstrap", is_architect=True)
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    yield user
    set_current_user_id(None)
    set_token_scope("read-write")


def _four_element_ops() -> list[dict]:
    names = [
        ("Payment API", "container", "technology"),
        ("Order Service", "container", "technology"),
        ("Order Domain", "component", "application"),
        ("Billing Worker", "component", "application"),
    ]
    return [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": name,
                "stereotype_slug": st,
                "package_slug": pkg,
            },
            "confidence": 0.95,
        }
        for name, st, pkg in names
    ]


def _non_manifest_ops() -> list[dict]:
    return [
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


class _FakeLLM:
    model_id = "fake-munin"

    def complete(self, messages, system="", max_tokens=1024, temperature=0.2):
        from yggdrasil.llm.base import LLMResponse

        payload = [
            {
                "source_name": "Service A",
                "target_name": "Service B",
                "stereotype_slug": "depends_on",
                "confidence": 0.9,
            }
        ]
        return LLMResponse(content=json.dumps(payload), model=self.model_id)


@pytest.mark.django_db
def test_bootstrap_planner_adds_relationship_ops() -> None:
    """CLI-04: four manifest elements yield relationship ops via scripted Munin."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="BootstrapTest", slug="bootstrap-test", metamodel=mm)
    ops = _four_element_ops()
    llm = build_munin_planning_llm()
    merged, summary = plan_bootstrap_changeset(
        model_id=model.pk, element_ops=ops, user_id=1, llm=llm
    )
    rel_ops = [op for op in merged if op["op_type"] == ChangeSetItem.OP_ADD_RELATIONSHIP]
    assert len(rel_ops) >= 1
    assert "add-relationship" in summary
    assert "source=llm" in summary or "source=manifest_scripted" in summary


@pytest.mark.django_db
def test_bootstrap_planner_llm_infers_relationship_ops() -> None:
    """LLM inference produces relationships for non-manifest element names."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="BootstrapLLM", slug="bootstrap-llm", metamodel=mm)
    ops = _non_manifest_ops()
    merged, summary = plan_bootstrap_changeset(
        model_id=model.pk,
        element_ops=ops,
        user_id=1,
        llm=_FakeLLM(),
    )
    rel_ops = [op for op in merged if op["op_type"] == ChangeSetItem.OP_ADD_RELATIONSHIP]
    assert len(rel_ops) == 1
    assert rel_ops[0]["detail"]["source_name"] == "Service A"
    assert "add-relationship" in summary
    assert "source=llm" in summary


@pytest.mark.django_db
def test_bootstrap_planner_manifest_fallback_only_when_scripted() -> None:
    """Manifest edges apply only for scripted Munin, not real-provider fake LLM."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="BootstrapManifest", slug="bootstrap-manifest", metamodel=mm)
    ops = _four_element_ops()

    class _EmptyLLM:
        model_id = "empty-provider"

        def complete(self, messages, system="", max_tokens=1024, temperature=0.2):
            from yggdrasil.llm.base import LLMResponse

            return LLMResponse(content="[]", model=self.model_id)

    empty_merged, empty_summary = plan_bootstrap_changeset(
        model_id=model.pk,
        element_ops=ops,
        user_id=1,
        llm=_EmptyLLM(),
    )
    empty_rels = [op for op in empty_merged if op["op_type"] == ChangeSetItem.OP_ADD_RELATIONSHIP]
    assert empty_rels == []
    assert "source=none" in empty_summary

    scripted_merged, scripted_summary = plan_bootstrap_changeset(
        model_id=model.pk,
        element_ops=ops,
        user_id=1,
        llm=ScriptedMuninLLM(),
    )
    scripted_rels = [
        op for op in scripted_merged if op["op_type"] == ChangeSetItem.OP_ADD_RELATIONSHIP
    ]
    assert len(scripted_rels) >= 1
    assert "source=llm" in scripted_summary or "source=manifest_scripted" in scripted_summary


def test_should_enrich_ratatosk_element_only_ops() -> None:
    """Planner runs for ratatosk element-only handoffs."""
    ops = _four_element_ops()
    assert should_enrich_ratatosk_ops(ChangeSet.SOURCE_RATATOSK, ops) is True


@pytest.mark.django_db
def test_propose_changeset_ratatosk_invokes_planner(rw_user) -> None:
    """Integration: propose_changeset summary contains add-relationship ops."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = propose_changeset(
        model="yggdrasil",
        operations=_four_element_ops(),
        source=ChangeSet.SOURCE_RATATOSK,
        run_id="run-cli04",
    )
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    assert "add-relationship" in (cs.munin_reasoning or "")
    rel_items = cs.items.filter(op_type=ChangeSetItem.OP_ADD_RELATIONSHIP)
    assert rel_items.count() >= 1
    assert result["applied_count"] >= 4


@pytest.mark.django_db
def test_propose_changeset_non_manifest_names_get_relationships_via_llm(rw_user) -> None:
    """Full MCP handoff infers relationships for non-fixture element names."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    with patch(
        "yggdrasil.munin.llm_factory.build_munin_planning_llm",
        return_value=_FakeLLM(),
    ):
        result = propose_changeset(
            model="yggdrasil",
            operations=_non_manifest_ops(),
            source=ChangeSet.SOURCE_RATATOSK,
            run_id="run-non-manifest",
        )
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    assert "source=llm" in (cs.munin_reasoning or "")
    assert cs.items.filter(op_type=ChangeSetItem.OP_ADD_RELATIONSHIP).count() >= 1


@pytest.mark.django_db
def test_propose_changeset_logs_munin_model_id(rw_user, caplog) -> None:
    """propose_changeset logs Munin llm_model and relationship source."""
    import logging

    caplog.set_level(logging.INFO)
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    with patch(
        "yggdrasil.munin.llm_factory.build_munin_planning_llm",
        return_value=_FakeLLM(),
    ):
        propose_changeset(
            model="yggdrasil",
            operations=_non_manifest_ops(),
            source=ChangeSet.SOURCE_RATATOSK,
            run_id="run-log-model",
        )
    combined = caplog.text
    assert "llm_model=" in combined
    assert "source=llm" in combined


@pytest.mark.django_db
def test_propose_changeset_relationships_on_graph(rw_user) -> None:
    """Applied relationships exist after auto-approve."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    propose_changeset(
        model="yggdrasil",
        operations=_four_element_ops(),
        source=ChangeSet.SOURCE_RATATOSK,
        run_id="run-rel-graph",
    )
    assert Element.objects.filter(model__slug="yggdrasil").count() == 4
    assert Relationship.objects.filter(model__slug="yggdrasil").count() >= 1


@pytest.mark.django_db
def test_propose_changeset_skips_relationships_for_below_threshold_elements(rw_user) -> None:
    """Munin must not wire edges to elements below auto-apply confidence."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())

    class _LowConfEdgeLLM:
        model_id = "fake-munin"

        def complete(self, messages, system="", max_tokens=1024, temperature=0.2):
            from yggdrasil.llm.base import LLMResponse

            payload = [
                {
                    "source_name": "Service A",
                    "target_name": "Low Confidence",
                    "stereotype_slug": "depends_on",
                    "confidence": 0.9,
                }
            ]
            return LLMResponse(content=json.dumps(payload), model=self.model_id)

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
                "name": "Low Confidence",
                "stereotype_slug": "component",
                "package_slug": "application",
            },
            "confidence": 0.5,
        },
    ]
    with patch(
        "yggdrasil.munin.llm_factory.build_munin_planning_llm",
        return_value=_LowConfEdgeLLM(),
    ):
        result = propose_changeset(
            model="yggdrasil",
            operations=ops,
            source=ChangeSet.SOURCE_RATATOSK,
            run_id="run-low-conf-edge",
            confidence_threshold=0.80,
        )
    assert result["applied_count"] == 1
    assert result["pending_count"] == 1
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    assert cs.items.filter(op_type=ChangeSetItem.OP_ADD_RELATIONSHIP).count() == 0
