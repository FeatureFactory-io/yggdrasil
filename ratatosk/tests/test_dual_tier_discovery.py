"""Unit tests for dual-tier discovery wiring in runner."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from ratatosk.discovery.limits import DiscoveryLimits
from ratatosk.discovery.runner import _llm_project_map, run_cli_discovery


class _TierTrackingLLM:
    """Records which tier invoked complete."""

    def __init__(self, tier: str, response: str) -> None:
        self.tier = tier
        self.model_id = f"mock-{tier}"
        self._response = response
        self.calls: list[str] = []

    def complete(
        self, messages, system: str = "", max_tokens: int = 1024, temperature: float = 0.2
    ):
        self.calls.append(self.tier)
        content = messages[-1].content if messages else ""
        if "Cluster hints" in content or "synthesizing bootstrap" in system:
            synth = {
                "canonical": [
                    {
                        "name": "Payment API",
                        "stereotype": "container",
                        "package": "technology",
                        "confidence": 0.9,
                        "source_paths": ["README.md"],
                    }
                ],
                "merges": [],
                "rejects": [],
                "notes": "test",
            }
            return MagicMock(content=json.dumps(synth))
        return MagicMock(content=self._response)


def test_llm_project_map_prompt_includes_max_targets() -> None:
    """Planning prompt tells Sonnet how many paths it may request."""
    planning = _TierTrackingLLM("planning", '{"project_kind":"web","targets":["README.md"]}')
    tree = ["README.md", "src/a.py"]
    limits = DiscoveryLimits(max_extract_targets=75, max_file_reads_per_run=1000)
    _llm_project_map(planning, tree, ontology="# c4", limits=limits, instructions="focus infra")
    assert planning.calls == ["planning"]
    # Re-invoke to capture last message via a fresh mock with stored messages
    captured: list[str] = []

    class _CaptureLLM:
        model_id = "capture"

        def complete(self, messages, system: str = "", **kwargs):
            captured.append(messages[-1].content)
            return MagicMock(content='{"project_kind":"web","targets":["README.md"]}')

    _llm_project_map(_CaptureLLM(), tree, ontology="# c4", limits=limits)
    assert "75" in captured[0]
    assert "docs/architecture/SAO.md" in captured[0]


def test_run_cli_discovery_records_llm_tiers_on_blackboard() -> None:
    """Blackboard captures planning vs extract model ids."""
    planning = _TierTrackingLLM(
        "planning",
        '{"project_kind":"fixture","targets":["README.md"]}',
    )
    extract = _TierTrackingLLM(
        "extract",
        '[{"name":"Payment API","stereotype":"container","package":"technology","confidence":0.9}]',
    )
    recorded: dict = {}

    class _Client:
        def call_tool(self, name: str, arguments: dict):
            if name == "ensure_model":
                return {"slug": "yggdrasil", "metamodel": "c4", "created": False}
            if name == "list_elements":
                return {"items": [], "total": 0}
            if name == "list_relationships":
                return {"items": [], "total": 0}
            if name == "list_stereotypes":
                return {
                    "items": [
                        {"slug": "container", "name": "Container", "is_edge": False},
                        {"slug": "component", "name": "Component", "is_edge": False},
                    ]
                }
            if name == "propose_changeset":
                return {
                    "changeset_id": 1,
                    "operations_count": 1,
                    "applied_count": 1,
                    "pending_count": 0,
                    "status": "applied",
                    "munin_reasoning": "source=llm",
                }
            if name == "record_ratatosk_run":
                recorded.update(arguments.get("blackboard") or {})
                return {"run_id": arguments.get("run_id")}
            raise AssertionError(name)

    limits = DiscoveryLimits(max_extract_targets=50, max_file_reads_per_run=1000)
    run_cli_discovery(
        client=_Client(),
        llm=extract,
        planning_llm=planning,
        extract_llm=extract,
        discovery_limits=limits,
        mode="filesystem",
        model_name="Yggdrasil",
        metamodel="c4",
        repo_path="tests/fixtures/repos/sample_webapp",
    )
    assert recorded["llm_tiers"]["planning_model"] == "mock-planning"
    assert recorded["llm_tiers"]["extract_model"] == "mock-extract"
    assert recorded["discovery_limits"]["max_extract_targets"] == 50
    assert "synthesize" in recorded
    assert recorded["synthesize"]["canonical_count"] >= 1
    assert "prefilter" in recorded


def test_run_cli_discovery_passes_handoff_context_to_propose() -> None:
    """propose_changeset receives synthesis handoff_context from runner."""
    planning = _TierTrackingLLM(
        "planning",
        '{"project_kind":"fixture","targets":["README.md"]}',
    )
    extract = _TierTrackingLLM(
        "extract",
        '[{"name":"Payment API","stereotype":"container","package":"technology","confidence":0.9}]',
    )
    propose_args: dict = {}

    class _Client:
        def call_tool(self, name: str, arguments: dict):
            if name == "ensure_model":
                return {"slug": "yggdrasil", "metamodel": "c4", "created": False}
            if name == "list_elements":
                return {"items": [], "total": 0}
            if name == "list_relationships":
                return {"items": [], "total": 0}
            if name == "list_stereotypes":
                return {
                    "items": [
                        {"slug": "container", "name": "Container", "is_edge": False},
                        {"slug": "component", "name": "Component", "is_edge": False},
                    ]
                }
            if name == "propose_changeset":
                propose_args.update(arguments)
                return {
                    "changeset_id": 1,
                    "operations_count": 1,
                    "applied_count": 1,
                    "pending_count": 0,
                    "status": "applied",
                }
            if name == "record_ratatosk_run":
                return {"run_id": arguments.get("run_id")}
            raise AssertionError(name)

    limits = DiscoveryLimits(max_extract_targets=50, max_file_reads_per_run=1000)
    run_cli_discovery(
        client=_Client(),
        llm=extract,
        planning_llm=planning,
        extract_llm=extract,
        discovery_limits=limits,
        mode="filesystem",
        model_name="Yggdrasil",
        metamodel="c4",
        repo_path="tests/fixtures/repos/sample_webapp",
    )
    ctx = propose_args.get("handoff_context") or {}
    assert "synthesize" in ctx
    assert "metamodel_slug" in ctx
    assert ctx["metamodel_slug"] == "c4"
