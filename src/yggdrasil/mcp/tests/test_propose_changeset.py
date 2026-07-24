"""Tests for MCP propose_changeset and record_ratatosk_run."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset, record_ratatosk_run
from yggdrasil.ratatosk.models import RataskRun


@pytest.fixture
def rw_user(db):
    """Architect user with ContextVar write scope."""
    user = UserFactory(username="priya-propose", is_architect=True)
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    yield user
    set_current_user_id(None)
    set_token_scope("read-write")


@pytest.mark.django_db
def test_propose_changeset_creates_pending(rw_user) -> None:
    """Ops → ChangeSet source=ratatosk with item count."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = propose_changeset(
        model="yggdrasil",
        operations=[
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": "Payment API",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.95,
            }
        ],
        run_id="run-propose-1",
    )
    assert result["changeset_id"]
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    assert cs.source == ChangeSet.SOURCE_RATATOSK
    assert cs.items.count() == 1
    assert result["applied_count"] == 1


@pytest.mark.django_db
def test_propose_changeset_rejects_readonly_token(rw_user) -> None:
    """Read-only scope → PermissionError; no ChangeSet."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    set_token_scope("read-only")
    before = ChangeSet.objects.count()
    with pytest.raises(PermissionError, match="permission"):
        propose_changeset(
            model="yggdrasil",
            operations=[
                {
                    "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                    "detail": {
                        "name": "X",
                        "stereotype_slug": "container",
                        "package_slug": "technology",
                    },
                    "confidence": 0.9,
                }
            ],
            run_id="run-ro",
        )
    assert ChangeSet.objects.count() == before


@pytest.mark.django_db
def test_propose_changeset_allow_empty(rw_user) -> None:
    """allow_empty=True → ChangeSet with 0 items."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = propose_changeset(
        model="yggdrasil",
        operations=[],
        allow_empty=True,
        run_id="run-empty",
    )
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    assert cs.items.count() == 0
    assert result["operations_count"] == 0


@pytest.mark.django_db
def test_propose_changeset_auto_applies_above_threshold(rw_user) -> None:
    """CLI-05: high-conf applied, low-conf pending."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    ops = []
    for idx in range(9):
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": f"High {idx}",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.9,
            }
        )
    for idx in range(2):
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": f"Low {idx}",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.5,
            }
        )
    result = propose_changeset(
        model="yggdrasil",
        operations=ops,
        confidence_threshold=0.80,
        run_id="run-threshold",
    )
    assert result["applied_count"] == 9
    assert result["pending_count"] == 2


@pytest.mark.django_db
def test_propose_changeset_builds_munin_llm_for_enrichment(rw_user) -> None:
    """Ratatosk handoff builds Munin planning LLM before bootstrap planner runs."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
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
    fake_llm = object()
    with (
        patch(
            "yggdrasil.munin.llm_factory.build_munin_planning_llm",
            return_value=fake_llm,
        ) as factory_mock,
        patch(
            "yggdrasil.munin.bootstrap_planner.plan_bootstrap_changeset",
            return_value=(
                ops,
                "Bootstrap handoff: 2 add-element ops, 1 add-relationship ops (source=llm)",
            ),
        ) as planner_mock,
    ):
        propose_changeset(
            model="yggdrasil",
            operations=ops,
            source=ChangeSet.SOURCE_RATATOSK,
            run_id="run-factory",
        )
    factory_mock.assert_called_once()
    assert planner_mock.call_args.kwargs["llm"] is fake_llm


@pytest.mark.django_db
def test_record_ratatosk_run_persists_blackboard(rw_user) -> None:
    """DISC-02: blackboard keys survive record_ratatosk_run."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = record_ratatosk_run(
        model="yggdrasil",
        run_id="run-bb-1",
        repo_path="./repo",
        blackboard={"tree": {"paths": ["docker-compose.yml"]}, "extract": {"candidates": 2}},
        status=RataskRun.STATUS_COMPLETE,
        trigger="bootstrap",
    )
    run = RataskRun.objects.get(run_id=result["run_id"])
    assert "tree" in run.blackboard
    assert "docker-compose.yml" in run.blackboard["tree"]["paths"]
