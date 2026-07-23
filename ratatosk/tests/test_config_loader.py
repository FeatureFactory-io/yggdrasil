"""Tests for ratatosk.config loader (ACT-1-CFG-06..13)."""

from __future__ import annotations

import pytest

from ratatosk.config import (
    BootstrapConfig,
    _resolve_base_model,
    build_llm_from_config,
    load_bootstrap_config,
)
from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM
from yggdrasil.llm.adapters.anthropic import AnthropicClient
from yggdrasil.llm.base import LLMError


def test_load_config_llm_provider_ollama_from_env() -> None:
    """CFG-06: LLM_PROVIDER=ollama maps to llm_provider key."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "ollama"})
    assert config.llm_provider == "ollama"


def test_load_config_llm_provider_anthropic_from_env() -> None:
    """CFG-10: LLM_PROVIDER=anthropic maps to llm_provider key."""
    config = load_bootstrap_config(
        env={"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"}
    )
    assert config.llm_provider == "anthropic"


def test_load_config_server_url_from_env() -> None:
    """CFG-09: YGGDRASIL_SERVER_URL is loaded."""
    config = load_bootstrap_config(
        env={"YGGDRASIL_SERVER_URL": "http://localhost:8000", "LLM_PROVIDER": "scripted"}
    )
    assert config.yggdrasil_server_url == "http://localhost:8000"


def test_load_config_ollama_url_and_model() -> None:
    """CFG-07: Ollama URL and model from env."""
    config = load_bootstrap_config(
        env={
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
            "LLM_OLLAMA_MODEL": "qwen3:14b",
        }
    )
    assert config.ollama_base_url == "http://127.0.0.1:11434"
    assert config.resolved_model == "qwen3:14b"


def test_load_config_metamodel_from_flags() -> None:
    """CFG-09: metamodel flag override."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "scripted"}, flags={"metamodel": "c4"})
    assert config.metamodel == "c4"


def test_load_config_default_provider_is_ollama_not_scripted() -> None:
    """CFG-08: empty env defaults to ollama provider."""
    config = load_bootstrap_config(env={})
    assert config.llm_provider == "ollama"
    assert config.resolved_model == "qwen3:14b"


def test_build_llm_scripted_only_when_explicit() -> None:
    """Scripted LLM only when LLM_PROVIDER=scripted."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "scripted"})
    llm = build_llm_from_config(config)
    assert isinstance(llm, ScriptedDiscoveryLLM)


def test_build_llm_no_silent_fallback_when_ollama_requested(monkeypatch) -> None:
    """CFG-06: ollama provider must not silently fall back to scripted."""
    import yggdrasil.llm.adapters.ollama as ollama_mod

    class _BrokenOllama:
        def __init__(self, *args, **kwargs):
            raise ImportError("no ollama")

    monkeypatch.setattr(ollama_mod, "OllamaClient", _BrokenOllama)
    config = load_bootstrap_config(env={"LLM_PROVIDER": "ollama"})
    with pytest.raises(RuntimeError, match="ollama"):
        build_llm_from_config(config)


def test_resolve_base_model_haiku_for_anthropic() -> None:
    """CFG-11: BASE_MODEL=haiku resolves to haiku API id."""
    resolved = _resolve_base_model("anthropic", "haiku", {})
    assert "haiku" in resolved


def test_resolve_base_model_sonnet5_alias() -> None:
    """CFG-11: sonnet5 alias maps to concrete Claude Sonnet id."""
    resolved = _resolve_base_model("anthropic", "sonnet5", {})
    assert resolved.startswith("claude")


def test_resolve_base_model_qwen_passthrough() -> None:
    """Ollama tag passes through unchanged."""
    resolved = _resolve_base_model("ollama", "qwen3:14b", {})
    assert resolved == "qwen3:14b"


def test_resolve_base_model_unknown_alias_raises() -> None:
    """Unknown anthropic alias raises ValueError."""
    with pytest.raises(ValueError, match="bogus"):
        _resolve_base_model("anthropic", "bogus", {})


def test_resolve_base_model_legacy_env_override() -> None:
    """LLM_ANTHROPIC_MODEL wins over BASE_MODEL when set."""
    resolved = _resolve_base_model(
        "anthropic",
        "haiku",
        {"LLM_ANTHROPIC_MODEL": "claude-custom-model"},
    )
    assert resolved == "claude-custom-model"


def test_build_llm_returns_anthropic_client_when_configured(monkeypatch) -> None:
    """CFG-10: anthropic provider returns AnthropicClient."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    config = BootstrapConfig(
        llm_provider="anthropic",
        resolved_model="claude-haiku-4-5-20251001",
    )
    llm = build_llm_from_config(config)
    assert isinstance(llm, AnthropicClient)


def test_build_llm_anthropic_missing_key_raises(monkeypatch) -> None:
    """LLM-06: missing API key fails fast."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = BootstrapConfig(llm_provider="anthropic", resolved_model="claude-3-5-haiku-20241022")
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        build_llm_from_config(config)


def test_load_config_repo_yaml_sets_llm_provider_and_model(tmp_path) -> None:
    """CFG-12: repo YAML sets llm_provider and resolved_model."""
    repo = tmp_path / "repo"
    cfg_dir = repo / ".ratatosk"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text(
        "llm_provider: ollama\nbase_model: qwen3:14b\n",
        encoding="utf-8",
    )
    config = load_bootstrap_config(env={}, repo_path=str(repo))
    assert config.llm_provider == "ollama"
    assert config.resolved_model == "qwen3:14b"


def test_load_config_env_overrides_repo_yaml(tmp_path) -> None:
    """CFG-13: env LLM_PROVIDER overrides repo YAML."""
    repo = tmp_path / "repo"
    cfg_dir = repo / ".ratatosk"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text("llm_provider: ollama\n", encoding="utf-8")
    config = load_bootstrap_config(
        env={"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-test"},
        repo_path=str(repo),
    )
    assert config.llm_provider == "anthropic"


def test_load_config_resolved_model_from_base_model_haiku() -> None:
    """CFG-11: load_bootstrap_config populates resolved_model."""
    config = load_bootstrap_config(
        env={
            "LLM_PROVIDER": "anthropic",
            "BASE_MODEL": "haiku",
            "ANTHROPIC_API_KEY": "sk-test",
        }
    )
    assert "haiku" in config.resolved_model
