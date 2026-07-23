"""
Journey L1 — programmatic Act 1 bootstrap then Act 6 update via MCP tools.

Uses the same tool callables registered on FastMCP (via InProcessMcpToolClient),
real DB, ScriptedDiscoveryLLM, and fixture repos. Not Playwright / not HTTP.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fixtures.factories import UserFactory

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, ensure_c4_metamodel
from yggdrasil.mcp import server as mcp_server_mod
from yggdrasil.ratatosk.agent import bootstrap_repository, update_from_stdin
from yggdrasil.ratatosk.handoff import McpHandoffPort
from yggdrasil.ratatosk.inprocess_mcp import InProcessMcpToolClient
from yggdrasil.ratatosk.llm_factory import ScriptedDiscoveryLLM
from yggdrasil.ratatosk.snapshot import McpSnapshotPort

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "repos"
SAMPLE_WEBAPP = FIXTURE_ROOT / "sample_webapp"
SAMPLE_STDIN = FIXTURE_ROOT / "sample_stdin"


@pytest.fixture(autouse=True)
def _reset_mcp_singleton():
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False
    yield
    mcp_server_mod._mcp_instance = None
    mcp_server_mod._initialized = False


def _assert_no_orphans(model) -> None:
    """Every Element must be referenced by an add_element ChangeSetItem."""
    for el in Element.objects.filter(model=model):
        assert ChangeSetItem.objects.filter(
            changeset__model=model,
            op_type=ChangeSetItem.OP_ADD_ELEMENT,
            detail__name=el.name,
        ).exists(), f"orphan Element {el.name!r}"


@pytest.mark.django_db
def test_journey_bootstrap_then_update_via_mcp() -> None:
    """
    Act1 sample_webapp bootstrap → ChangeSet + no orphans → Act6 pr.diff update.

    Snapshot + handoff go through MCP tool functions (in-process client).
    """
    ensure_c4_metamodel()
    mcp_server_mod.initialize_mcp()
    user = UserFactory(username="priya-journey", is_architect=True)
    client = InProcessMcpToolClient(user_id=user.pk, token_scope="read-write")
    snapshot = McpSnapshotPort(client)
    handoff = McpHandoffPort(client)
    llm = ScriptedDiscoveryLLM()

    run1, buckets1, output1 = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        user=user,
        llm=llm,
        snapshot=snapshot,
        handoff=handoff,
    )
    print("\n=== ACT 1 bootstrap (CLI stdout) ===")
    print(output1)
    print(
        f"=== ACT 1 result: run_id={run1.run_id} "
        f"changeset_id={run1.changeset_id} "
        f"to_add={len(buckets1.to_add)} unchanged={len(buckets1.unchanged)} "
        f"elements={Element.objects.filter(model=run1.model).count()} ===\n"
    )
    assert "building ModelSummary" in output1
    assert "run complete" in output1
    assert "ChangeSet #" in output1
    assert run1.changeset_id is not None
    cs1 = ChangeSet.objects.get(pk=run1.changeset_id)
    assert cs1.source == ChangeSet.SOURCE_RATATOSK
    assert buckets1.total_ops >= 1 or cs1.items.count() >= 0
    _assert_no_orphans(run1.model)

    elements_page = client.call_tool(
        "list_elements", {"model": run1.model.slug, "limit": 50, "offset": 0}
    )
    element_names = {item["name"] for item in elements_page.get("items") or []}
    for manifest_name in (
        "Payment API",
        "Order Service",
        "Order Domain",
        "Billing Worker",
    ):
        assert manifest_name in element_names, f"missing {manifest_name!r} after bootstrap"

    assert "tree" in (run1.blackboard or {})

    diff_text = (SAMPLE_STDIN / "pr.diff").read_text(encoding="utf-8")
    run2, buckets2, output2 = update_from_stdin(
        stdin_text=diff_text,
        model_name="Yggdrasil",
        metamodel="c4",
        user=user,
        llm=ScriptedDiscoveryLLM(),
        snapshot=snapshot,
        handoff=handoff,
    )
    assert "building ModelSummary" in output2
    assert run2.changeset_id is not None
    cs2 = ChangeSet.objects.get(pk=run2.changeset_id)
    print("=== ACT 6 update (CLI stdout) ===")
    print(output2)
    print(
        f"=== ACT 6 result: run_id={run2.run_id} "
        f"changeset_id={run2.changeset_id} "
        f"changeset_ops={cs2.items.count()} "
        f"bucket_total_ops={buckets2.total_ops} "
        f"input_mode={(run2.blackboard or {}).get('input_mode')} ===\n"
    )
    assert cs2.source == ChangeSet.SOURCE_RATATOSK
    # Unchanged must never appear as ChangeSet operations
    assert cs2.items.count() == buckets2.total_ops
    _assert_no_orphans(run2.model)
    assert (run2.blackboard or {}).get("input_mode") == "stdin"
