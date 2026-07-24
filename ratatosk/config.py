"""Ratatosk CLI configuration loader (no Django imports)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

from ratatosk.discovery.exclude import normalize_exclude_patterns
from ratatosk.discovery.limits import (
    DEFAULT_MAX_EXTRACT_TARGETS,
    DEFAULT_MAX_FILE_READS_PER_RUN,
    MAX_EXTRACT_TARGETS_CEILING,
    MAX_FILE_READS_PER_RUN_CEILING,
    DiscoveryLimits,
    clamp_int_limit,
)

logger = logging.getLogger("ratatosk.config")

_DEFAULT_SERVER = "https://yggdrasil.featurefactory.io"
_DEFAULT_OLLAMA_URL = "http://localhost:11434"
_DEFAULT_OLLAMA_MODEL = "qwen3:14b"
_DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_METAMODEL = "c4"
_DEFAULT_BUDGET = 8000
_DEFAULT_PROVIDER = "ollama"

_DEFAULT_PLANNING_ALIAS = "sonnet5"

_YAML_ALLOWLIST = frozenset(
    {
        "llm_provider",
        "base_model",
        "planning_model",
        "ollama_base_url",
        "model_summary_token_budget",
        "max_extract_targets",
        "max_file_reads_per_run",
        "exclude",
        "instructions",
    }
)

_MODEL_ALIASES: dict[str, dict[str, str]] = {
    "anthropic": {
        "haiku": _DEFAULT_ANTHROPIC_MODEL,
        "sonnet5": "claude-sonnet-4-5-20250929",
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
    exclude_patterns: list[str] = field(default_factory=list)
    instructions: str = ""
    planning_model: str = ""
    resolved_planning_model: str = ""
    max_extract_targets: int = DEFAULT_MAX_EXTRACT_TARGETS
    max_file_reads_per_run: int = DEFAULT_MAX_FILE_READS_PER_RUN
    extra_env: dict[str, str] = field(default_factory=dict)

    @property
    def discovery_limits(self) -> DiscoveryLimits:
        """Scout bounds for bootstrap extract loop."""
        return DiscoveryLimits(
            max_extract_targets=self.max_extract_targets,
            max_file_reads_per_run=self.max_file_reads_per_run,
        )


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

    exclude_raw = flags.get("exclude") or raw.get("RATATOSK_EXCLUDE") or yaml_layer.get("exclude")
    exclude_patterns = normalize_exclude_patterns(
        exclude_raw if isinstance(exclude_raw, list) else str(exclude_raw or "")
    )

    instructions_flag = str(flags.get("instructions") or "").strip()
    instructions_yaml = str(yaml_layer.get("instructions") or "").strip()
    instructions = instructions_flag or instructions_yaml

    planning_raw = str(
        raw.get("RATATOSK_PLANNING_MODEL") or yaml_layer.get("planning_model") or ""
    ).strip()
    if provider == "scripted":
        resolved_planning = resolved
    elif provider == "ollama":
        resolved_planning = (
            _resolve_base_model(provider, planning_raw, raw) if planning_raw else resolved
        )
    else:
        resolved_planning = _resolve_base_model(
            provider,
            planning_raw or _DEFAULT_PLANNING_ALIAS,
            raw,
        )

    max_extract = clamp_int_limit(
        raw.get("RATATOSK_MAX_EXTRACT_TARGETS") or yaml_layer.get("max_extract_targets"),
        default=DEFAULT_MAX_EXTRACT_TARGETS,
        ceiling=MAX_EXTRACT_TARGETS_CEILING,
        name="max_extract_targets",
    )
    max_file_reads = clamp_int_limit(
        raw.get("RATATOSK_MAX_FILE_READS_PER_RUN") or yaml_layer.get("max_file_reads_per_run"),
        default=DEFAULT_MAX_FILE_READS_PER_RUN,
        ceiling=MAX_FILE_READS_PER_RUN_CEILING,
        name="max_file_reads_per_run",
    )

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
        exclude_patterns=exclude_patterns,
        instructions=instructions,
        planning_model=planning_raw,
        resolved_planning_model=resolved_planning,
        max_extract_targets=max_extract,
        max_file_reads_per_run=max_file_reads,
    )
    logger.info(
        "load_bootstrap_config | llm_provider=%s base_model=%r resolved_model=%s "
        "planning_model=%r resolved_planning_model=%s max_extract_targets=%s "
        "max_file_reads_per_run=%s ollama_base_url=%s",
        config.llm_provider,
        config.base_model,
        config.resolved_model,
        config.planning_model,
        config.resolved_planning_model,
        config.max_extract_targets,
        config.max_file_reads_per_run,
        config.ollama_base_url,
    )
    return config


def build_llm_from_config(config: BootstrapConfig, *, model: str | None = None):
    """
    Instantiate field-tier (extract) discovery LLM from config.

    :param config: Loaded bootstrap config.
    :param model: Optional override model id (planning tier passes its resolved id).
    :return: LLM client with ``complete`` method.
    :raises RuntimeError: When provider cannot be constructed.
    :raises LLMError: When anthropic provider lacks API key.
    """
    return _build_llm_client(config, model or config.resolved_model, tier="extract")


def build_extract_llm_from_config(config: BootstrapConfig):
    """
    Alias for field-tier extract LLM (Haiku / fast model).

    :param config: Loaded bootstrap config.
    :return: LLM client with ``complete`` method.
    """
    return build_llm_from_config(config)


def build_planning_llm_from_config(config: BootstrapConfig):
    """
    Instantiate planning-tier LLM for ``_llm_project_map``.

    :param config: Loaded bootstrap config.
    :return: LLM client with ``complete`` method.
    """
    return _build_llm_client(config, config.resolved_planning_model, tier="planning")


def _build_llm_client(config: BootstrapConfig, model_id: str, *, tier: str):
    from ratatosk.discovery.scripted_llm import ScriptedDiscoveryLLM
    from yggdrasil.llm.base import LLMError

    provider = config.llm_provider
    logger.info(
        "_build_llm_client | tier=%s provider=%s model_id=%s",
        tier,
        provider,
        model_id,
    )
    if provider == "scripted":
        client = ScriptedDiscoveryLLM()
        logger.info("_build_llm_client | tier=%s client=%s", tier, type(client).__name__)
        return client
    if provider == "ollama":
        try:
            from yggdrasil.llm.adapters.ollama import OllamaClient

            client = OllamaClient(model=model_id, base_url=config.ollama_base_url)
            logger.info("_build_llm_client | tier=%s client=%s", tier, type(client).__name__)
            return client
        except Exception as exc:
            msg = f"LLM_PROVIDER=ollama but Ollama client failed: {exc}"
            logger.error("_build_llm_client | tier=%s %s", tier, msg)
            raise RuntimeError(msg) from exc
    if provider == "anthropic":
        api_key = str(os.environ.get("ANTHROPIC_API_KEY") or "").strip()
        if not api_key:
            msg = "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set"
            logger.error("_build_llm_client | tier=%s reason=missing_api_key", tier)
            raise LLMError(msg)
        from yggdrasil.llm.adapters.anthropic import AnthropicClient

        client = AnthropicClient(model=model_id, api_key=api_key)
        logger.info("_build_llm_client | tier=%s client=%s", tier, type(client).__name__)
        return client
    msg = f"Unknown LLM_PROVIDER={provider!r}; use scripted, ollama, or anthropic"
    raise RuntimeError(msg)
