"""Pytest for unified Ratatosk discovery (filesystem + stdin) with FakeLLM."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.fixtures.factories.model_factories import (
    ElementFactory,
    PackageFactory,
    StereotypeFactory,
    YggdrasilModelFactory,
)

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, ensure_c4_metamodel
from yggdrasil.llm.base import LLMResponse
from yggdrasil.ratatosk.agent import (
    DiscoveryInput,
    RataskAgent,
    bootstrap_repository,
    update_from_stdin,
)
from yggdrasil.ratatosk.llm_factory import ScriptedDiscoveryLLM
from yggdrasil.ratatosk.models import RataskRun
from yggdrasil.ratatosk.snapshot import LocalOrmSnapshotPort, McpSnapshotPort, normalize_snapshot

FIXTURE_ROOT = Path(__file__).resolve().parents[4] / "tests" / "fixtures" / "repos"
SAMPLE_WEBAPP = FIXTURE_ROOT / "sample_webapp"
SAMPLE_STDIN = FIXTURE_ROOT / "sample_stdin"
EMPTY_REPO = FIXTURE_ROOT / "empty_repo"


class FakeLLM:
    """Multi-turn fake LLM with call counting (DISC-05)."""

    model_id = "fake"

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    def complete(self, messages, system="", max_tokens=1024, temperature=0.2) -> LLMResponse:
        self.call_count += 1
        if not self._responses:
            return LLMResponse(content="[]", model=self.model_id)
        content = self._responses.pop(0)
        return LLMResponse(content=content, model=self.model_id)


class FakeSnapshot:
    """Snapshot double returning fixture counts (ACT-6-CICD-03)."""

    def __init__(self, element_count: int = 0, relationship_count: int = 0) -> None:
        self.calls: list[str] = []
        self._element_count = element_count
        self._relationship_count = relationship_count
        self.fail = False

    def fetch_model(self, model_slug: str) -> dict:
        self.calls.append(model_slug)
        if self.fail:
            raise RuntimeError("MCP snapshot failed: connection refused")
        elements = [
            {
                "id": i,
                "name": f"Element {i}",
                "slug": f"element-{i}",
                "owner": "",
                "stereotype__name": "Container",
                "package__name": "Technology",
            }
            for i in range(self._element_count)
        ]
        relationships = [{"id": i} for i in range(self._relationship_count)]
        return normalize_snapshot(elements, relationships)


class FakeMcpClient:
    """MCP client double for McpSnapshotPort."""

    def __init__(self, *, fail: bool = False, elements: list[dict] | None = None) -> None:
        self.fail = fail
        self.elements = elements or []
        self.calls: list[str] = []

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        self.calls.append(name)
        if self.fail:
            raise RuntimeError("MCP unreachable")
        if name == "list_elements":
            return {"items": self.elements, "total": len(self.elements)}
        if name == "list_relationships":
            return {"items": [], "total": 0}
        if name in {"propose_changeset", "record_ratatosk_run"}:
            return {"changeset_id": 1, "status": "pending", "run_id": "run-fake"}
        raise RuntimeError(f"unknown tool {name}")


def _map_json(targets: list[str]) -> str:
    return json.dumps({"project_kind": "python-web", "targets": targets})


def _candidates_json(extra: dict | None = None) -> str:
    items = [
        {
            "name": "Payment API",
            "stereotype": "container",
            "package": "technology",
            "confidence": 0.95,
        },
        {
            "name": "Order Domain",
            "stereotype": "component",
            "package": "application",
            "confidence": 0.92,
        },
    ]
    if extra:
        items.append(extra)
    return json.dumps(items)


@pytest.mark.django_db
def test_bootstrap_discovers_containers_and_components_from_fixture() -> None:
    """DISC-01: fixture repo yields Container/Component via ChangeSet."""
    ensure_c4_metamodel()
    llm = ScriptedDiscoveryLLM()
    run, buckets, output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=llm,
        snapshot=LocalOrmSnapshotPort(),
    )
    assert run.status == RataskRun.STATUS_COMPLETE
    assert buckets.total_ops >= 1
    assert "building ModelSummary" in output
    assert ChangeSet.objects.filter(source=ChangeSet.SOURCE_RATATOSK).exists()
    stereotypes = set(
        Element.objects.filter(model=run.model).values_list("stereotype__name", flat=True)
    )
    assert "Container" in stereotypes or buckets.to_add
    assert llm.call_count >= 1


@pytest.mark.django_db
def test_blackboard_has_tree_before_extract() -> None:
    """DISC-02: blackboard records tree paths before extract."""
    ensure_c4_metamodel()
    run, _buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    board = run.blackboard
    assert "tree" in board
    assert "docker-compose.yml" in board["tree"]["paths"]
    assert "extract" in board
    assert "project_map" in board


@pytest.mark.django_db
def test_existing_model_yields_delta_buckets() -> None:
    """DISC-03: re-bootstrap wipes pre-seeded Payment API then rescans."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    st = StereotypeFactory(metamodel=mm, name="Container", slug="container", is_edge=False)
    pkg = PackageFactory(metamodel=mm, name="Technology", slug="technology")
    ElementFactory(
        model=model,
        name="Payment API",
        slug="payment-api",
        stereotype=st,
        package=pkg,
    )
    _run, buckets, output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    assert "wiping" in output
    assert "to_add:" in output
    assert "unchanged:" not in output
    assert len(buckets.to_delete) >= 1
    assert len(buckets.to_add) >= 1
    assert buckets.unchanged == []


@pytest.mark.django_db
def test_cleanup_drops_unknown_stereotype() -> None:
    """DISC-04: microservice never reaches Munin / model."""
    ensure_c4_metamodel()
    llm = ScriptedDiscoveryLLM(
        extra_candidate={
            "name": "Invented Microservice",
            "stereotype": "microservice",
            "package": "technology",
            "confidence": 0.99,
        }
    )
    run, _buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=llm,
        snapshot=LocalOrmSnapshotPort(),
    )
    assert not Element.objects.filter(stereotype__slug="microservice").exists()
    cs = run.changeset
    assert cs is not None
    for item in cs.items.all():
        detail = item.detail or {}
        assert detail.get("stereotype_slug") != "microservice"


@pytest.mark.django_db
def test_discovery_uses_llm_turns_not_hardcoded_fallback() -> None:
    """DISC-05: FakeLLM multi-turn is invoked; project_map on blackboard."""
    ensure_c4_metamodel()
    targets = [
        "docker-compose.yml",
        "README.md",
        "src/order_domain/service.py",
    ]
    fake = FakeLLM(
        responses=[_map_json(targets), _candidates_json(), _candidates_json(), _candidates_json()]
    )
    run, buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=fake,
        snapshot=LocalOrmSnapshotPort(),
    )
    assert fake.call_count >= 1
    assert "project_map" in run.blackboard
    assert buckets.total_ops >= 1


@pytest.mark.django_db
def test_no_orphan_elements_outside_changeset() -> None:
    """DISC-06: every new Element is tied to a ChangeSetItem add op."""
    ensure_c4_metamodel()
    run, _buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    assert run.changeset is not None
    assert run.changeset.source == ChangeSet.SOURCE_RATATOSK
    for el in Element.objects.filter(model=run.model):
        assert ChangeSetItem.objects.filter(
            changeset__model=run.model,
            op_type=ChangeSetItem.OP_ADD_ELEMENT,
            detail__name=el.name,
        ).exists(), f"orphan Element {el.name!r} has no ChangeSetItem"


@pytest.mark.django_db
def test_empty_repo_nothing_to_scan() -> None:
    """DISC-12: empty tree → nothing to scan, no invented elements."""
    ensure_c4_metamodel()
    run, buckets, output = bootstrap_repository(
        repo_path=str(EMPTY_REPO),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    assert "nothing to scan" in output
    assert buckets.total_ops == 0
    assert Element.objects.filter(model=run.model).count() == 0


@pytest.mark.django_db
def test_mcp_snapshot_failure_no_orm_fallback() -> None:
    """DISC-13: MCP failure raises; no orphan Elements."""
    ensure_c4_metamodel()
    snap = FakeSnapshot()
    snap.fail = True
    with pytest.raises(RuntimeError, match="MCP"):
        bootstrap_repository(
            repo_path=str(SAMPLE_WEBAPP),
            model_name="Yggdrasil",
            metamodel="c4",
            llm=ScriptedDiscoveryLLM(),
            snapshot=snap,
        )
    assert Element.objects.count() == 0


@pytest.mark.django_db
def test_non_json_llm_plan_no_hardcoded_elements() -> None:
    """DISC-14: non-JSON LLM → empty plan / no architecture changes; no orphans."""
    ensure_c4_metamodel()
    fake = FakeLLM(
        responses=[
            "I am not JSON at all",
            "still prose",
            "nope",
            "definitely not candidates",
        ]
    )
    # Map returns non-JSON → falls back to tree targets; extracts also prose → []
    run, buckets, output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=fake,
        snapshot=LocalOrmSnapshotPort(),
    )
    assert buckets.total_ops == 0
    assert "no architecture changes detected" in output or "empty plan" in output
    assert Element.objects.filter(model=run.model).count() == 0


@pytest.mark.django_db
def test_unknown_metamodel_slug_fails() -> None:
    """DISC-09: unknown metamodel → ValueError, no wrong Model binding."""
    with pytest.raises(ValueError, match="metamodel"):
        bootstrap_repository(
            repo_path=str(SAMPLE_WEBAPP),
            model_name="Yggdrasil",
            metamodel="no-such-mm",
            llm=ScriptedDiscoveryLLM(),
            snapshot=LocalOrmSnapshotPort(),
        )


@pytest.mark.django_db
def test_metamodel_mismatch_fails() -> None:
    """DISC-10: --metamodel mismatches bound Model."""
    from tests.fixtures.factories.model_factories import MetamodelFactory

    c4 = ensure_c4_metamodel()
    other = MetamodelFactory(name="Other", slug="other")
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=c4)
    with pytest.raises(ValueError, match="bound to metamodel"):
        bootstrap_repository(
            repo_path=str(SAMPLE_WEBAPP),
            model_name="Yggdrasil",
            metamodel=other.slug,
            llm=ScriptedDiscoveryLLM(),
            snapshot=LocalOrmSnapshotPort(),
        )


@pytest.mark.django_db
def test_read_only_token_fails_before_handoff() -> None:
    """DISC-08: read-only scope → PermissionError."""
    ensure_c4_metamodel()
    with pytest.raises(PermissionError, match="permission"):
        bootstrap_repository(
            repo_path=str(SAMPLE_WEBAPP),
            model_name="Yggdrasil",
            metamodel="c4",
            llm=ScriptedDiscoveryLLM(),
            snapshot=LocalOrmSnapshotPort(),
            require_write_token=True,
            token_scope="read-only",
        )


@pytest.mark.django_db
def test_update_prose_stdin() -> None:
    """CICD-08: README prose on stdin → delta + blackboard stdin kind."""
    ensure_c4_metamodel()
    text = (SAMPLE_STDIN / "architecture-notes.md").read_text(encoding="utf-8")
    run, buckets, output = update_from_stdin(
        stdin_text=text,
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    assert run.blackboard.get("input_mode") == "stdin"
    assert run.blackboard.get("stdin_kind") == "prose"
    assert "building ModelSummary" in output
    assert buckets.total_ops >= 1 or run.changeset is not None


@pytest.mark.django_db
def test_update_noise_diff_no_ops() -> None:
    """CICD-07/14: test-file noise → 0 ops + message."""
    ensure_c4_metamodel()
    text = (SAMPLE_STDIN / "noise-only.diff").read_text(encoding="utf-8")
    # Force empty extract for noise
    fake = FakeLLM(responses=['{"focus": [], "summary": "tests only"}', "[]"])
    run, buckets, output = update_from_stdin(
        stdin_text=text,
        model_name="Yggdrasil",
        metamodel="c4",
        llm=fake,
        snapshot=LocalOrmSnapshotPort(),
    )
    assert buckets.total_ops == 0
    assert "no architecture changes detected" in output
    assert run.changeset is not None
    assert run.changeset.items.count() == 0


@pytest.mark.django_db
def test_update_empty_stdin() -> None:
    """CICD-09: empty stdin → no architecture changes."""
    ensure_c4_metamodel()
    _run, buckets, output = update_from_stdin(
        stdin_text="",
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    assert buckets.total_ops == 0
    assert "no architecture changes detected" in output


@pytest.mark.django_db
def test_update_stdin_over_size_cap() -> None:
    """CICD-10: oversize stdin → ValueError about limit."""
    ensure_c4_metamodel()
    from yggdrasil.ratatosk.agent import STDIN_SIZE_CAP_BYTES

    huge = "x" * (STDIN_SIZE_CAP_BYTES + 10)
    with pytest.raises(ValueError, match="limit"):
        update_from_stdin(
            stdin_text=huge,
            model_name="Yggdrasil",
            metamodel="c4",
            llm=ScriptedDiscoveryLLM(),
            snapshot=LocalOrmSnapshotPort(),
        )


@pytest.mark.django_db
def test_update_mcp_failure_no_changeset() -> None:
    """CICD-12: MCP fail mid-update → no ChangeSet."""
    ensure_c4_metamodel()
    snap = FakeSnapshot()
    snap.fail = True
    before = ChangeSet.objects.count()
    with pytest.raises(RuntimeError, match="MCP"):
        update_from_stdin(
            stdin_text=(SAMPLE_STDIN / "pr.diff").read_text(encoding="utf-8"),
            model_name="Yggdrasil",
            metamodel="c4",
            llm=ScriptedDiscoveryLLM(),
            snapshot=snap,
        )
    assert ChangeSet.objects.count() == before


@pytest.mark.django_db
def test_mcp_snapshot_port_calls_list_elements() -> None:
    """MCP snapshot uses list_elements (CICD-03 plumbing)."""
    client = FakeMcpClient(
        elements=[
            {"id": 1, "name": "Payment API", "slug": "payment-api", "stereotype": "Container"}
        ]
    )
    port = McpSnapshotPort(client)
    snap = port.fetch_model("yggdrasil")
    assert "list_elements" in client.calls
    assert snap["element_count"] == 1
    assert "payment-api" in snap["by_slug"]


@pytest.mark.django_db
def test_agent_execute_filesystem_loop_directly() -> None:
    """Agent blackboard steps for filesystem mode."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    run = RataskRun.objects.create(
        model=model,
        run_id="run-test-fs",
        repo_path=str(SAMPLE_WEBAPP),
        status=RataskRun.STATUS_RUNNING,
    )
    agent = RataskAgent(
        llm=ScriptedDiscoveryLLM(),
        run=run,
        snapshot=LocalOrmSnapshotPort(),
    )
    buckets = agent.execute(DiscoveryInput(mode="filesystem", repo_path=str(SAMPLE_WEBAPP)))
    assert "tree" in run.blackboard
    assert "cleanup" in run.blackboard
    assert buckets is not None


@pytest.mark.django_db
def test_disc15_blackboard_has_model_summary_chars() -> None:
    """DISC-15: model_summary key on blackboard after bootstrap."""
    ensure_c4_metamodel()
    run, _buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    summary = (run.blackboard or {}).get("model_summary") or {}
    assert "model_summary_chars" in summary
    assert int(summary["model_summary_chars"]) > 0


@pytest.mark.django_db
def test_disc15_summary_under_budget() -> None:
    """DISC-15: ModelSummary chars within 8000-token proxy budget."""
    ensure_c4_metamodel()
    run, _buckets, _output = bootstrap_repository(
        repo_path=str(SAMPLE_WEBAPP),
        model_name="Yggdrasil",
        metamodel="c4",
        llm=ScriptedDiscoveryLLM(),
        snapshot=LocalOrmSnapshotPort(),
    )
    chars = int((run.blackboard or {}).get("model_summary", {}).get("model_summary_chars", 0))
    assert chars <= 8000 * 4
