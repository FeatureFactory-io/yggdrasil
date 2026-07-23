"""Tests for Munin bootstrap handoff (ACT-1-CLI-04)."""

from __future__ import annotations

import pytest
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, Relationship, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset
from yggdrasil.munin.bootstrap_planner import plan_bootstrap_changeset, should_enrich_ratatosk_ops


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


def test_bootstrap_planner_adds_relationship_ops() -> None:
    """CLI-04: four manifest elements yield relationship ops."""
    ops = _four_element_ops()
    merged, summary = plan_bootstrap_changeset(model_id=1, element_ops=ops, user_id=1)
    rel_ops = [op for op in merged if op["op_type"] == ChangeSetItem.OP_ADD_RELATIONSHIP]
    assert len(rel_ops) >= 1
    assert "add-relationship" in summary


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
