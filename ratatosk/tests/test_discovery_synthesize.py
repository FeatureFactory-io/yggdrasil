"""Tests for ratatosk.discovery.synthesize."""

from __future__ import annotations

from unittest.mock import MagicMock

from ratatosk.discovery.synthesize import _llm_synthesize_candidates, apply_synthesis


def test_synthesize_apply_merges_backend_aliases() -> None:
    """Backend dropped; Backend container kept in canonical list."""
    candidates = [
        {
            "name": "Backend",
            "stereotype": "container",
            "confidence": 0.9,
            "source_paths": ["README.md"],
        },
        {
            "name": "Backend container",
            "stereotype": "container",
            "confidence": 0.95,
            "source_paths": ["docs/architecture/SAO.md"],
        },
    ]
    synthesis = {
        "canonical": [
            {
                "name": "Backend container",
                "stereotype": "container",
                "package": "technology",
                "confidence": 0.95,
                "source_paths": ["docs/architecture/SAO.md", "README.md"],
            }
        ],
        "merges": [{"drop": "Backend", "keep": "Backend container", "reason": "SAO canonical"}],
        "rejects": [],
        "notes": "merged duplicate backend names",
    }
    canonical, meta = apply_synthesis(candidates, synthesis)
    assert len(canonical) == 1
    assert canonical[0]["name"] == "Backend container"
    assert "Backend" in meta["do_not_reference"]


def test_llm_synthesize_prompt_includes_cluster_hints() -> None:
    """Synthesize prompt includes cluster hints and candidate count."""
    captured: list[str] = []

    class _CaptureLLM:
        model_id = "capture-planning"

        def complete(self, messages, system="", **kwargs):
            captured.append(messages[-1].content)
            return MagicMock(content='{"canonical":[],"merges":[],"rejects":[],"notes":""}')

    candidates = [
        {
            "name": "Backend",
            "stereotype": "container",
            "confidence": 0.9,
            "source_paths": ["README.md"],
        },
        {
            "name": "Backend container",
            "stereotype": "container",
            "confidence": 0.95,
            "source_paths": ["docs/architecture/SAO.md"],
        },
    ]
    hints = {"backend": ["Backend", "Backend container"]}
    _llm_synthesize_candidates(_CaptureLLM(), candidates, "# c4", hints, instructions="focus SAO")
    assert captured
    assert "backend" in captured[0].lower() or "Backend container" in captured[0]
    assert "Candidates (2)" in captured[0]
