"""Tests for ratatosk.config loader (ACT-1-CFG-06..13)."""

from __future__ import annotations

import pytest

from ratatosk.config import (
    BootstrapConfig,
    _resolve_base_model,
    build_extract_llm_from_config,
    build_llm_from_config,
    build_planning_llm_from_config,
    load_bootstrap_config,
)
from ratatosk.discovery.limits import (
    DEFAULT_MAX_EXTRACT_TARGETS,
    DEFAULT_MAX_FILE_READS_PER_RUN,
    MAX_EXTRACT_TARGETS_CEILING,
)
from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM
from yggdrasil.llm.adapters.anthropic import AnthropicClient
from yggdrasil.llm.base import LLMError, LLMMessage, LLMRequestOptions


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


def test_load_config_llm_provider_openai_defaults_and_aliases() -> None:
    """OpenAI gets its own default model and provider-specific aliases."""
    default = load_bootstrap_config(env={"LLM_PROVIDER": "openai"})
    fast = load_bootstrap_config(env={"LLM_PROVIDER": "openai", "BASE_MODEL": "openai_fast"})
    assert default.resolved_model == "gpt-5.6-terra"
    assert fast.resolved_model == "gpt-5.6-luna"


def test_load_config_openai_rejects_claude_alias() -> None:
    """Claude aliases are not silently mapped to OpenAI models."""
    with pytest.raises(ValueError, match="provider openai"):
        load_bootstrap_config(env={"LLM_PROVIDER": "openai", "BASE_MODEL": "sonnet5"})


def test_load_config_openai_accepts_opaque_compatible_model_and_base_url() -> None:
    """Ratatosk retains a local Responses model ID and endpoint unchanged."""
    model_id = "gemma-4-e4b-uncensored-hauhaucs-aggressive"
    config = load_bootstrap_config(
        env={
            "LLM_PROVIDER": "openai",
            "BASE_MODEL": model_id,
            "OPENAI_BASE_URL": "http://127.0.0.1:1234/v1",
        }
    )
    assert config.resolved_model == model_id
    assert config.openai_base_url == "http://127.0.0.1:1234/v1"


def test_load_config_openai_planning_tier_ignores_base_model_legacy_override() -> None:
    """An explicit planning model remains independent from the extract-model override."""
    config = load_bootstrap_config(
        env={
            "LLM_PROVIDER": "openai",
            "LLM_OPENAI_MODEL": "gpt-extract",
            "RATATOSK_PLANNING_MODEL": "gpt-plan",
        }
    )
    assert config.resolved_model == "gpt-extract"
    assert config.resolved_planning_model == "gpt-plan"


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


def test_cli_scripted_discovery_options_preserve_provider_contract() -> None:
    """Empty options are accepted; unsupported options fail without consuming a reply."""
    llm = ScriptedDiscoveryLLM()
    message = LLMMessage(role="user", content="find candidates")

    result = llm.complete([message], options=LLMRequestOptions())

    assert result.content
    assert llm.call_count == 1
    with pytest.raises(LLMError, match="does not support"):
        llm.complete([message], options=LLMRequestOptions(reasoning_effort="low"))
    assert llm.call_count == 1


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


def test_build_llm_returns_openai_client_when_configured(monkeypatch) -> None:
    """OpenAI provider selects OpenAIClient without importing another adapter."""
    from yggdrasil.llm.adapters import openai as openai_module

    class _FakeOpenAI:
        def __init__(self, model: str, api_key: str, *, base_url: str | None = None) -> None:
            self.model_id = model
            self.api_key = api_key
            self.base_url = base_url

    monkeypatch.setattr(openai_module, "OpenAIClient", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    config = BootstrapConfig(llm_provider="openai", resolved_model="gpt-test")
    llm = build_llm_from_config(config)
    assert isinstance(llm, _FakeOpenAI)
    assert llm.model_id == "gpt-test"


def test_build_llm_passes_openai_base_url_to_client(monkeypatch) -> None:
    """Ratatosk forwards the explicit compatible endpoint to OpenAIClient."""
    from yggdrasil.llm.adapters import openai as openai_module

    class _FakeOpenAI:
        def __init__(self, model: str, api_key: str, *, base_url: str | None = None) -> None:
            self.model_id = model
            self.base_url = base_url

    monkeypatch.setattr(openai_module, "OpenAIClient", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "local-test")
    config = BootstrapConfig(
        llm_provider="openai",
        resolved_model="gemma-local",
        openai_base_url="http://127.0.0.1:1234/v1",
    )
    llm = build_llm_from_config(config)
    assert llm.base_url == "http://127.0.0.1:1234/v1"


def test_build_llm_anthropic_missing_key_raises(monkeypatch) -> None:
    """LLM-06: missing API key fails fast."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = BootstrapConfig(llm_provider="anthropic", resolved_model="claude-3-5-haiku-20241022")
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        build_llm_from_config(config)


def test_build_llm_openai_missing_key_raises(monkeypatch) -> None:
    """OpenAI provider fails fast without a key and does not fall back."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = BootstrapConfig(llm_provider="openai", resolved_model="gpt-test")
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
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


def test_load_config_exclude_from_env() -> None:
    """RATATOSK_EXCLUDE merges into exclude_patterns."""
    config = load_bootstrap_config(env={"RATATOSK_EXCLUDE": "src/payment_api/,docs/"})
    assert config.exclude_patterns == ["src/payment_api/", "docs/"]


def test_load_config_defaults_max_extract_targets_50() -> None:
    """Unset env yields default max_extract_targets=50."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "scripted"})
    assert config.max_extract_targets == DEFAULT_MAX_EXTRACT_TARGETS


def test_load_config_defaults_max_file_reads_1000() -> None:
    """Unset env yields SAO-aligned max_file_reads_per_run=1000."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "scripted"})
    assert config.max_file_reads_per_run == DEFAULT_MAX_FILE_READS_PER_RUN


def test_load_config_clamps_max_extract_targets_at_ceiling() -> None:
    """Values above 1000 clamp with warning semantics (stored as ceiling)."""
    config = load_bootstrap_config(
        env={"LLM_PROVIDER": "scripted", "RATATOSK_MAX_EXTRACT_TARGETS": "5000"}
    )
    assert config.max_extract_targets == MAX_EXTRACT_TARGETS_CEILING


def test_load_config_max_extract_targets_from_env() -> None:
    """CFG-14: RATATOSK_MAX_EXTRACT_TARGETS=75 is honored."""
    config = load_bootstrap_config(
        env={"LLM_PROVIDER": "scripted", "RATATOSK_MAX_EXTRACT_TARGETS": "75"}
    )
    assert config.max_extract_targets == 75


def test_load_config_resolved_planning_model_sonnet5_default() -> None:
    """Anthropic default planning tier resolves sonnet5 alias."""
    config = load_bootstrap_config(
        env={"LLM_PROVIDER": "anthropic", "BASE_MODEL": "haiku", "ANTHROPIC_API_KEY": "sk-test"}
    )
    assert "sonnet" in config.resolved_planning_model.lower()
    assert "haiku" in config.resolved_model.lower()


def test_build_planning_and_extract_llm_differ_for_anthropic(monkeypatch) -> None:
    """Planning and extract clients use different resolved model ids."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    config = load_bootstrap_config(
        env={
            "LLM_PROVIDER": "anthropic",
            "BASE_MODEL": "haiku",
            "RATATOSK_PLANNING_MODEL": "sonnet5",
        }
    )
    planning = build_planning_llm_from_config(config)
    extract = build_extract_llm_from_config(config)
    assert planning.model_id == config.resolved_planning_model
    assert extract.model_id == config.resolved_model
    assert planning.model_id != extract.model_id


def test_build_extract_llm_alias_matches_build_llm_from_config(monkeypatch) -> None:
    """build_extract_llm_from_config is an alias of build_llm_from_config."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    config = load_bootstrap_config(env={"LLM_PROVIDER": "anthropic", "BASE_MODEL": "haiku"})
    assert type(build_extract_llm_from_config(config)) is type(build_llm_from_config(config))


def test_load_config_instructions_cli_overrides_yaml(tmp_path) -> None:
    """Non-empty CLI instructions override repo YAML."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "ratatosk.yaml").write_text(
        "instructions: from yaml\nexclude:\n  - docs/\n",
        encoding="utf-8",
    )
    config = load_bootstrap_config(
        repo_path=str(repo),
        flags={"instructions": "from cli"},
    )
    assert config.instructions == "from cli"
    assert "docs/" in config.exclude_patterns
