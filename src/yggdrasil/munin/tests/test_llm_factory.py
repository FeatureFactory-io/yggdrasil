"""Tests for Munin planning-tier LLM factory."""

from __future__ import annotations

from django.test import override_settings

from yggdrasil.munin.llm_factory import (
    ScriptedMuninLLM,
    build_munin_planning_llm,
    munin_allows_manifest_fallback,
    resolve_munin_planning_model,
)


def test_resolve_munin_planning_model_defaults_to_sonnet5() -> None:
    """Munin default alias is sonnet5, not Ratatosk haiku."""
    with override_settings(MUNIN_PLANNING_MODEL="sonnet5"):
        resolved = resolve_munin_planning_model(provider="anthropic")
    assert resolved == "claude-sonnet-4-5-20250929"


def test_build_munin_planning_llm_scripted_in_tests() -> None:
    """Test settings use scripted Munin LLM."""
    llm = build_munin_planning_llm()
    assert isinstance(llm, ScriptedMuninLLM)
    assert llm.model_id == "scripted-munin"
    assert munin_allows_manifest_fallback(llm) is True


def test_build_munin_planning_llm_injected_passthrough() -> None:
    """Explicit injection bypasses factory resolution."""
    sentinel = object()
    assert build_munin_planning_llm(llm=sentinel) is sentinel


def test_scripted_munin_returns_bootstrap_relationship_json() -> None:
    """Scripted Munin emits manifest edges for bootstrap relationship prompts."""
    from yggdrasil.llm.base import LLMMessage

    llm = ScriptedMuninLLM()
    response = llm.complete(
        messages=[
            LLMMessage(
                role="user",
                content=(
                    "Given these architecture elements from a bootstrap scan, return relationship "
                    'objects.\n\nElements: ["Order Domain", "Order Service", "Payment API"]'
                ),
            )
        ]
    )
    import json

    payload = json.loads(response.content)
    assert isinstance(payload, list)
    assert len(payload) >= 1
