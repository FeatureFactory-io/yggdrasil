"""Ratatosk CLI configuration loader (no Django imports)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

logger = logging.getLogger("ratatosk.config")

_DEFAULT_SERVER = "https://yggdrasil.featurefactory.io"
_DEFAULT_OLLAMA_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "qwen3:14b"
_DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-20241022"
_DEFAULT_METAMODEL = "c4"
_DEFAULT_BUDGET = 8000
_DEFAULT_PROVIDER = "ollama"

_YAML_ALLOWLIST = frozenset(
    {"llm_provider", "base_model", "ollama_base_url", "model_summary_token_budget"}
)

_MODEL_ALIASES: dict[str, dict[str, str]] = {
    "anthropic": {
        "haiku": _DEFAULT_ANTHROPIC_MODEL,
        "sonnet5": "claude-sonnet-4-20250514",
    },
    "ollama": {},
}


@dataclass(frozen=True)
class BootstrapConfig:
    """Effective configuration for bootstrap/update CLI runs."""

    llm_provider: str = _DEFAULT_PROVIDER
    yggdrasil_server_url: str = _DEFAULT_SERVER
    yggdrasil_token: str = ""
    base_model: str = ""
    resolved_model: str = _DEFAULT_OLLAMA_MODEL
    llm_ollama_model: str = _DEFAULT_OLLAMA_MODEL
    ollama_base_url: str = _DEFAULT_OLLAMA_URL
    metamodel: str = _DEFAULT_METAMODEL
    model_summary_token_budget: int = _DEFAULT_BUDGET
    extra_env: dict[str, str] = field(default_factory=dict)


def _resolve_base_model(provider: str, raw: str, env: Mapping[str, str]) -> str:
    """
    Resolve BASE_MODEL alias to a concrete provider model id.

    :param provider: ``ollama`` or ``anthropic``.
    :param raw: Raw ``BASE_MODEL`` or YAML value (may be empty).
    :param env: Environment mapping for legacy overrides.
    :return: Concrete model id string.
    :raises ValueError: When alias is unknown for the provider.
    """
    if provider == "anthropic":
        legacy = str(env.get("LLM_ANTHROPIC_MODEL") or "").strip()
        if legacy:
            logger.info(
                "_resolve_base_model | provider=%s input=%r branch=legacy_env resolved_id=%s",
                provider,
                raw,
                legacy,
            )
            return legacy
    if provider == "ollama":
        legacy = str(env.get("LLM_OLLAMA_MODEL") or "").strip()
        if legacy:
            logger.info(
                "_resolve_base_model | provider=%s input=%r branch=legacy_env resolved_id=%s",
                provider,
                raw,
                legacy,
            )
            return legacy

    cleaned = str(raw or "").strip()
    if not cleaned:
        resolved = _DEFAULT_ANTHROPIC_MODEL if provider == "anthropic" else _DEFAULT_OLLAMA_MODEL
        logger.info(
            "_resolve_base_model | provider=%s input=(unset) branch=default resolved_id=%s",
            provider,
            resolved,
        )
        return resolved

    aliases = _MODEL_ALIASES.get(provider, {})
    if cleaned in aliases:
        resolved = aliases[cleaned]
        logger.info(
            "_resolve_base_model | provider=%s input=%s branch=alias resolved_id=%s",
            provider,
            cleaned,
            resolved,
        )
        return resolved

    if provider == "anthropic" and not cleaned.startswith("claude"):
        msg = f"Unknown BASE_MODEL alias {cleaned!r} for provider anthropic"
        logger.error("_resolve_base_model | %s", msg)
        raise ValueError(msg)

    logger.info(
        "_resolve_base_model | provider=%s input=%s branch=passthrough resolved_id=%s",
        provider,
        cleaned,
        cleaned,
    )
    return cleaned


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        return {}
    filtered = {k: v for k, v in data.items() if k in _YAML_ALLOWLIST}
    logger.info("_load_yaml_file | path=%s keys=%s", path, list(filtered))
    return filtered


def _load_yaml_layers(repo_path: str) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    home = Path.home() / ".ratatosk" / "config.yaml"
    merged.update(_load_yaml_file(home))
    if repo_path:
        root = Path(repo_path)
        for rel in (".ratatosk/config.yaml", "ratatosk.yaml"):
            merged.update(_load_yaml_file(root / rel))
    logger.info(
        "_load_yaml_layers | repo_path=%s merged_keys=%s", repo_path or "(none)", list(merged)
    )
    return merged


def load_bootstrap_config(
    *,
    env: Mapping[str, str] | None = None,
    repo_path: str = "",
    flags: dict[str, str | int | None] | None = None,
) -> BootstrapConfig:
    """
    Load bootstrap configuration from env (and optional repo/flags).

    Merge order: home YAML → repo YAML → env (wins).

    :param env: Environment mapping; defaults to ``os.environ``.
    :param repo_path: Repository path for ratatosk.yaml merge.
    :param flags: CLI flag overrides (server, metamodel, etc.).
    :return: Resolved :class:`BootstrapConfig`.
    """
    raw = dict(env if env is not None else os.environ)
    flags = flags or {}
    yaml_layer = _load_yaml_layers(repo_path)
    logger.info(
        "load_bootstrap_config | repo_path=%s sources=yaml+env%s",
        repo_path or "(none)",
        "+flags" if flags else "",
    )

    provider = (
        str(raw.get("LLM_PROVIDER") or yaml_layer.get("llm_provider") or _DEFAULT_PROVIDER)
        .strip()
        .lower()
        or _DEFAULT_PROVIDER
    )

    base_model = str(raw.get("BASE_MODEL") or yaml_layer.get("base_model") or "").strip()

    server = str(flags.get("server") or raw.get("YGGDRASIL_SERVER_URL") or _DEFAULT_SERVER).strip()
    token = str(raw.get("YGGDRASIL_TOKEN") or "").strip()
    ollama_url = str(
        raw.get("OLLAMA_BASE_URL")
        or raw.get("LLM_OLLAMA_URL")
        or yaml_layer.get("ollama_base_url")
        or _DEFAULT_OLLAMA_URL
    ).strip()
    resolved = _resolve_base_model(provider, base_model, raw)
    ollama_model = (
        resolved
        if provider == "ollama"
        else str(raw.get("LLM_OLLAMA_MODEL") or _DEFAULT_OLLAMA_MODEL).strip()
    )
    metamodel = str(flags.get("metamodel") or raw.get("RATATOSK_METAMODEL") or _DEFAULT_METAMODEL)
    budget_raw = (
        raw.get("MODEL_SUMMARY_TOKEN_BUDGET")
        or yaml_layer.get("model_summary_token_budget")
        or str(_DEFAULT_BUDGET)
    )
    try:
        budget = int(budget_raw)
    except (TypeError, ValueError):
        budget = _DEFAULT_BUDGET

    config = BootstrapConfig(
        llm_provider=provider,
        yggdrasil_server_url=server,
        yggdrasil_token=token,
        base_model=base_model,
        resolved_model=resolved,
        llm_ollama_model=ollama_model,
        ollama_base_url=ollama_url,
        metamodel=metamodel.strip().lower(),
        model_summary_token_budget=budget,
    )
    logger.info(
        "load_bootstrap_config | llm_provider=%s base_model=%r resolved_model=%s ollama_base_url=%s",
        config.llm_provider,
        config.base_model,
        config.resolved_model,
        config.ollama_base_url,
    )
    return config


def build_llm_from_config(config: BootstrapConfig):
    """
    Instantiate discovery LLM from config.

    :param config: Loaded bootstrap config.
    :return: LLM client with ``complete`` method.
    :raises RuntimeError: When provider cannot be constructed.
    :raises LLMError: When anthropic provider lacks API key.
    """
    from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM
    from yggdrasil.llm.base import LLMError

    provider = config.llm_provider
    logger.info(
        "build_llm_from_config | provider=%s resolved_model=%s",
        provider,
        config.resolved_model,
    )
    if provider == "scripted":
        client = ScriptedDiscoveryLLM()
        logger.info("build_llm_from_config | client=%s", type(client).__name__)
        return client
    if provider == "ollama":
        try:
            from yggdrasil.llm.adapters.ollama import OllamaClient

            client = OllamaClient(model=config.resolved_model, base_url=config.ollama_base_url)
            logger.info("build_llm_from_config | client=%s", type(client).__name__)
            return client
        except Exception as exc:
            msg = f"LLM_PROVIDER=ollama but Ollama client failed: {exc}"
            logger.error("build_llm_from_config | %s", msg)
            raise RuntimeError(msg) from exc
    if provider == "anthropic":
        api_key = str(os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            msg = "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set"
            logger.error("build_llm_from_config | reason=missing_api_key")
            raise LLMError(msg)
        from yggdrasil.llm.adapters.anthropic import AnthropicClient

        client = AnthropicClient(model=config.resolved_model, api_key=api_key)
        logger.info("build_llm_from_config | client=%s", type(client).__name__)
        return client
    msg = f"Unknown LLM_PROVIDER={provider!r}; use scripted, ollama, or anthropic"
    raise RuntimeError(msg)
