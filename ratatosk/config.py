"""Ratatosk CLI configuration loader (no Django imports)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Mapping

logger = logging.getLogger("ratatosk.config")

_DEFAULT_SERVER = "https://yggdrasil.featurefactory.io"
_DEFAULT_OLLAMA_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "qwen3:14b"
_DEFAULT_METAMODEL = "c4"
_DEFAULT_BUDGET = 8000


@dataclass(frozen=True)
class BootstrapConfig:
    """Effective configuration for bootstrap/update CLI runs."""

    llm_provider: str = "scripted"
    yggdrasil_server_url: str = _DEFAULT_SERVER
    yggdrasil_token: str = ""
    llm_ollama_model: str = _DEFAULT_OLLAMA_MODEL
    ollama_base_url: str = _DEFAULT_OLLAMA_URL
    metamodel: str = _DEFAULT_METAMODEL
    model_summary_token_budget: int = _DEFAULT_BUDGET
    extra_env: dict[str, str] = field(default_factory=dict)


def load_bootstrap_config(
    *,
    env: Mapping[str, str] | None = None,
    repo_path: str = "",
    flags: dict[str, str | int | None] | None = None,
) -> BootstrapConfig:
    """
    Load bootstrap configuration from env (and optional repo/flags).

    :param env: Environment mapping; defaults to ``os.environ``.
    :param repo_path: Repository path for future ratatosk.yaml merge.
    :param flags: CLI flag overrides (server, metamodel, etc.).
    :return: Resolved :class:`BootstrapConfig`.
    """
    raw = dict(env or os.environ)
    flags = flags or {}
    logger.info(
        "load_bootstrap_config | repo_path=%s sources=env%s",
        repo_path or "(none)",
        "+flags" if flags else "",
    )
    provider = str(raw.get("LLM_PROVIDER", "scripted")).strip().lower() or "scripted"
    server = str(flags.get("server") or raw.get("YGGDRASIL_SERVER_URL") or _DEFAULT_SERVER).strip()
    token = str(raw.get("YGGDRASIL_TOKEN") or "").strip()
    ollama_url = str(
        raw.get("OLLAMA_BASE_URL") or raw.get("LLM_OLLAMA_URL") or _DEFAULT_OLLAMA_URL
    ).strip()
    ollama_model = str(raw.get("LLM_OLLAMA_MODEL") or _DEFAULT_OLLAMA_MODEL).strip()
    metamodel = str(flags.get("metamodel") or raw.get("RATATOSK_METAMODEL") or _DEFAULT_METAMODEL)
    budget_raw = raw.get("MODEL_SUMMARY_TOKEN_BUDGET") or str(_DEFAULT_BUDGET)
    try:
        budget = int(budget_raw)
    except ValueError:
        budget = _DEFAULT_BUDGET

    config = BootstrapConfig(
        llm_provider=provider,
        yggdrasil_server_url=server,
        yggdrasil_token=token,
        llm_ollama_model=ollama_model,
        ollama_base_url=ollama_url,
        metamodel=metamodel.strip().lower(),
        model_summary_token_budget=budget,
    )
    logger.info(
        "load_bootstrap_config | llm_provider=%s server=%s ollama_base_url=%s model=%s",
        config.llm_provider,
        config.yggdrasil_server_url,
        config.ollama_base_url,
        config.llm_ollama_model,
    )
    return config


def build_llm_from_config(config: BootstrapConfig):
    """
    Instantiate discovery LLM from config.

    :param config: Loaded bootstrap config.
    :return: LLM client with ``complete`` method.
    :raises RuntimeError: When ``ollama`` provider cannot be constructed.
    """
    from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM

    provider = config.llm_provider
    logger.info("build_llm_from_config | provider=%s", provider)
    if provider == "scripted":
        return ScriptedDiscoveryLLM()
    if provider in {"", "auto"} or os.environ.get("RATATOSK_USE_SCRIPTED"):
        logger.info("build_llm_from_config | defaulting to scripted")
        return ScriptedDiscoveryLLM()
    if provider == "ollama":
        try:
            from yggdrasil.llm.adapters.ollama import OllamaClient

            return OllamaClient(model=config.llm_ollama_model, base_url=config.ollama_base_url)
        except Exception as exc:
            msg = f"LLM_PROVIDER=ollama but Ollama client failed: {exc}"
            logger.error("build_llm_from_config | %s", msg)
            raise RuntimeError(msg) from exc
    msg = f"Unknown LLM_PROVIDER={provider!r}; use scripted or ollama"
    raise RuntimeError(msg)
