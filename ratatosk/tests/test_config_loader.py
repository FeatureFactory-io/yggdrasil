"""Tests for ratatosk.config loader (ACT-1-CFG-06..09)."""

from __future__ import annotations

import pytest

from ratatosk.config import build_llm_from_config, load_bootstrap_config
from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM


def test_load_config_llm_provider_ollama_from_env() -> None:
    """CFG-06: LLM_PROVIDER=ollama maps to llm_provider key."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "ollama"})
    assert config.llm_provider == "ollama"


def test_load_config_server_url_from_env() -> None:
    """CFG-08: YGGDRASIL_SERVER_URL is loaded."""
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
    assert config.llm_ollama_model == "qwen3:14b"


def test_load_config_metamodel_from_flags() -> None:
    """CFG-09: metamodel flag override."""
    config = load_bootstrap_config(env={"LLM_PROVIDER": "scripted"}, flags={"metamodel": "c4"})
    assert config.metamodel == "c4"


def test_build_llm_returns_scripted_by_default() -> None:
    """Default provider is scripted for CI."""
    config = load_bootstrap_config(env={})
    llm = build_llm_from_config(config)
    assert isinstance(llm, ScriptedDiscoveryLLM)


def test_build_llm_no_silent_fallback_when_ollama_requested(monkeypatch) -> None:
    """CFG-06: ollama provider must not silently fall back to scripted."""
    import ratatosk.config as config_mod

    class _BrokenOllama:
        def __init__(self, *args, **kwargs):
            raise ImportError("no ollama")

    monkeypatch.setattr(config_mod, "OllamaClient", _BrokenOllama, raising=False)
    # Force import path used by build_llm_from_config
    import yggdrasil.llm.adapters.ollama as ollama_mod

    monkeypatch.setattr(ollama_mod, "OllamaClient", _BrokenOllama)
    config = load_bootstrap_config(env={"LLM_PROVIDER": "ollama"})
    with pytest.raises(RuntimeError, match="ollama"):
        build_llm_from_config(config)
