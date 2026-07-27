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


def test_resolve_munin_planning_model_openai_defaults_and_alias(monkeypatch) -> None:
    """OpenAI planning uses its own default and aliases."""
    monkeypatch.delenv("MUNIN_PLANNING_MODEL", raising=False)
    with override_settings(LLM_PROVIDER="openai", MUNIN_PLANNING_MODEL=""):
        default = resolve_munin_planning_model(provider="openai")
    with override_settings(LLM_PROVIDER="openai", MUNIN_PLANNING_MODEL="openai_quality"):
        quality = resolve_munin_planning_model(provider="openai")
    assert default == "gpt-5.6-terra"
    assert quality == "gpt-5.6-sol"


def test_resolve_munin_planning_model_openai_rejects_explicit_claude_alias(monkeypatch) -> None:
    """An explicit Claude alias cannot silently cross providers."""
    monkeypatch.setenv("MUNIN_PLANNING_MODEL", "sonnet5")
    with override_settings(LLM_PROVIDER="openai", MUNIN_PLANNING_MODEL="sonnet5"):
        import pytest

        with pytest.raises(ValueError, match="provider openai"):
            resolve_munin_planning_model(provider="openai")


def test_resolve_munin_planning_model_openai_accepts_opaque_compatible_model(monkeypatch) -> None:
    """Munin accepts a local Responses-compatible model ID without a GPT prefix."""
    monkeypatch.delenv("MUNIN_PLANNING_MODEL", raising=False)
    model_id = "gemma-4-e4b-uncensored-hauhaucs-aggressive"
    with override_settings(LLM_PROVIDER="openai", MUNIN_PLANNING_MODEL=model_id):
        assert resolve_munin_planning_model(provider="openai") == model_id


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


def test_build_munin_planning_llm_returns_openai_client(monkeypatch) -> None:
    """Munin selects OpenAIClient only for the OpenAI provider."""
    monkeypatch.delenv("MUNIN_PLANNING_MODEL", raising=False)
    from yggdrasil.llm.adapters import openai as openai_module

    class _FakeOpenAI:
        def __init__(self, model: str, api_key: str, *, base_url: str | None = None) -> None:
            self.model_id = model
            self.api_key = api_key
            self.base_url = base_url

    monkeypatch.setattr(openai_module, "OpenAIClient", _FakeOpenAI)
    with override_settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="sk-test",
        MUNIN_PLANNING_MODEL="",
    ):
        llm = build_munin_planning_llm()
    assert isinstance(llm, _FakeOpenAI)
    assert llm.model_id == "gpt-5.6-terra"


def test_build_munin_planning_llm_passes_openai_base_url(monkeypatch) -> None:
    """Munin forwards the same configured compatible endpoint to OpenAIClient."""
    monkeypatch.delenv("MUNIN_PLANNING_MODEL", raising=False)
    from yggdrasil.llm.adapters import openai as openai_module

    class _FakeOpenAI:
        def __init__(self, model: str, api_key: str, *, base_url: str | None = None) -> None:
            self.model_id = model
            self.base_url = base_url

    monkeypatch.setattr(openai_module, "OpenAIClient", _FakeOpenAI)
    with override_settings(
        LLM_PROVIDER="openai",
        OPENAI_API_KEY="local-test",
        OPENAI_BASE_URL="http://127.0.0.1:1234/v1",
        MUNIN_PLANNING_MODEL="gemma-local",
    ):
        llm = build_munin_planning_llm()
    assert llm.base_url == "http://127.0.0.1:1234/v1"


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
