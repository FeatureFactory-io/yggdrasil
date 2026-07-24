"""Munin planning-tier LLM factory (server-side, Django settings)."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from django.conf import settings

from yggdrasil.llm.base import LLMError, LLMMessage, LLMResponse
from yggdrasil.munin.logging_utils import log_munin_entry, log_munin_exit, log_munin_structure

logger = logging.getLogger("yggdrasil.munin.llm_factory")

_SCRIPTED_MODEL_ID = "scripted-munin"
_DEFAULT_MUNIN_ALIAS = "sonnet5"
_DEFAULT_ANTHROPIC_MUNIN = "claude-sonnet-4-5-20250929"
_DEFAULT_OLLAMA_MUNIN = "qwen3:14b"

_ANTHROPIC_ALIASES: dict[str, str] = {
    "sonnet5": _DEFAULT_ANTHROPIC_MUNIN,
    "haiku": "claude-haiku-4-5-20251001",
}

# sample_webapp manifest edges — AT/scripted bootstrap only
_SCRIPTED_BOOTSTRAP_EDGES: list[tuple[str, str, str]] = [
    ("Order Domain", "Order Service", "depends_on"),
    ("Billing Worker", "Order Domain", "depends_on"),
    ("Order Service", "Payment API", "depends_on"),
]


class ScriptedMuninLLM:
    """
    Deterministic Munin LLM for tests and behave ATs.

    Bootstrap relationship prompts return manifest edges when element names match.
    Chat and write-tool prompts return a short grounded placeholder.
    """

    model_id = _SCRIPTED_MODEL_ID

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Return scripted JSON for bootstrap inference or a chat placeholder."""
        prompt = messages[-1].content if messages else ""
        if _is_bootstrap_relationship_prompt(prompt):
            content = _scripted_bootstrap_relationships(prompt)
            from yggdrasil.munin.logging_utils import log_munin_llm_request, log_munin_llm_response

            log_munin_llm_request(
                where="llm_factory.ScriptedMuninLLM.complete",
                user_id=None,
                llm_model=self.model_id,
                system=system,
                prompt=prompt,
            )
            log_munin_llm_response(
                where="llm_factory.ScriptedMuninLLM.complete",
                user_id=None,
                llm_model=self.model_id,
                raw_content=content,
                parsed_count=len(json.loads(content)) if content.startswith("[") else 0,
                accepted_count=len(json.loads(content)) if content.startswith("[") else 0,
                rejected_count=0,
            )
            return LLMResponse(content=content, model=self.model_id)
        logger.info("ScriptedMuninLLM.complete | kind=chat_placeholder")
        return LLMResponse(content="Munin grounded response", model=self.model_id)


def build_munin_planning_llm(*, llm: Any | None = None) -> Any:
    """
    Resolve Munin planning-tier LLM from Django settings and environment.

    Default production model: ``sonnet5`` → ``claude-sonnet-4-5-20250929``.
    Ratatosk ``BASE_MODEL`` is never used for Munin.

    :param llm: Explicit injection for tests; returned unchanged when set.
    :return: LLM client implementing ``complete`` and ``model_id``.
    :raises LLMError: When anthropic provider lacks API key.
    :raises RuntimeError: When provider is unknown or client construction fails.
    """
    log_munin_entry(
        "build_munin_planning_llm",
        where="llm_factory.build_munin_planning_llm",
        llm_model=getattr(llm, "model_id", type(llm).__name__) if llm is not None else "",
    )
    if llm is not None:
        log_munin_exit(
            "build_munin_planning_llm",
            where="llm_factory.build_munin_planning_llm",
            success=True,
            branch="injected",
            llm_model=getattr(llm, "model_id", type(llm).__name__),
        )
        return llm

    provider = str(getattr(settings, "LLM_PROVIDER", "ollama")).strip().lower()
    munin_alias = str(getattr(settings, "MUNIN_PLANNING_MODEL", _DEFAULT_MUNIN_ALIAS)).strip()
    config_snapshot = {
        "llm_provider": provider,
        "munin_planning_model_alias": munin_alias,
        "ollama_base_url": str(getattr(settings, "OLLAMA_BASE_URL", "")),
        "anthropic_key_set": bool(str(getattr(settings, "ANTHROPIC_API_KEY", "") or "").strip()),
        "ratatosk_base_model_not_used": True,
    }
    log_munin_structure("munin_llm_config", config_snapshot)
    resolved_model = resolve_munin_planning_model(provider=provider)
    logger.info(
        "build_munin_planning_llm | provider=%s resolved_model=%s",
        provider,
        resolved_model,
    )

    if provider == "scripted":
        client = ScriptedMuninLLM()
        log_munin_exit(
            "build_munin_planning_llm",
            where="llm_factory.build_munin_planning_llm",
            success=True,
            client_class=type(client).__name__,
            llm_model=client.model_id,
        )
        return client

    if provider == "anthropic":
        api_key = str(getattr(settings, "ANTHROPIC_API_KEY", "") or "").strip()
        if not api_key:
            msg = "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set"
            logger.error("build_munin_planning_llm | reason=missing_api_key")
            raise LLMError(msg)
        from yggdrasil.llm.adapters.anthropic import AnthropicClient

        client = AnthropicClient(model=resolved_model, api_key=api_key)
        log_munin_exit(
            "build_munin_planning_llm",
            where="llm_factory.build_munin_planning_llm",
            success=True,
            client_class=type(client).__name__,
            llm_model=resolved_model,
        )
        return client

    if provider == "ollama":
        try:
            from yggdrasil.llm.adapters.ollama import OllamaClient

            base_url = str(getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434"))
            client = OllamaClient(model=resolved_model, base_url=base_url)
            log_munin_exit(
                "build_munin_planning_llm",
                where="llm_factory.build_munin_planning_llm",
                success=True,
                client_class=type(client).__name__,
                llm_model=resolved_model,
            )
            return client
        except Exception as exc:
            msg = f"LLM_PROVIDER=ollama but Ollama client failed: {exc}"
            logger.error("build_munin_planning_llm | %s", msg)
            raise RuntimeError(msg) from exc

    msg = f"Unknown LLM_PROVIDER={provider!r}; use scripted, ollama, or anthropic"
    raise RuntimeError(msg)


def resolve_munin_planning_model(*, provider: str) -> str:
    """
    Resolve ``MUNIN_PLANNING_MODEL`` to a concrete provider model id.

    :param provider: ``anthropic``, ``ollama``, or ``scripted``.
    :return: Concrete model id string.
    :raises ValueError: When anthropic alias is unknown.
    """
    raw = str(getattr(settings, "MUNIN_PLANNING_MODEL", _DEFAULT_MUNIN_ALIAS)).strip()
    legacy = str(os.environ.get("MUNIN_PLANNING_MODEL") or raw).strip() or _DEFAULT_MUNIN_ALIAS

    if provider == "anthropic":
        if legacy in _ANTHROPIC_ALIASES:
            resolved = _ANTHROPIC_ALIASES[legacy]
            logger.info(
                "resolve_munin_planning_model | provider=%s input=%s branch=alias resolved_id=%s",
                provider,
                legacy,
                resolved,
            )
            return resolved
        if legacy.startswith("claude"):
            logger.info(
                "resolve_munin_planning_model | provider=%s input=%s branch=passthrough",
                provider,
                legacy,
            )
            return legacy
        msg = f"Unknown MUNIN_PLANNING_MODEL alias {legacy!r} for provider anthropic"
        logger.error("resolve_munin_planning_model | %s", msg)
        raise ValueError(msg)

    if provider == "ollama":
        resolved = legacy if legacy not in _ANTHROPIC_ALIASES else _DEFAULT_OLLAMA_MUNIN
        logger.info(
            "resolve_munin_planning_model | provider=%s input=%s resolved_id=%s",
            provider,
            legacy,
            resolved,
        )
        return resolved

    logger.info(
        "resolve_munin_planning_model | provider=%s resolved_id=%s branch=scripted_or_other",
        provider,
        _SCRIPTED_MODEL_ID,
    )
    return _SCRIPTED_MODEL_ID


def munin_allows_manifest_fallback(llm: Any) -> bool:
    """True when manifest edges are permitted (scripted AT path only)."""
    return getattr(llm, "model_id", "") == _SCRIPTED_MODEL_ID


def _is_bootstrap_relationship_prompt(prompt: str) -> bool:
    lowered = prompt.lower()
    return "bootstrap scan" in lowered and "relationship" in lowered


def _scripted_bootstrap_relationships(prompt: str) -> str:
    """Build manifest relationship JSON for element names found in the prompt."""
    names = _parse_element_names_from_prompt(prompt)
    payload: list[dict[str, Any]] = []
    for source_name, target_name, edge_slug in _SCRIPTED_BOOTSTRAP_EDGES:
        if source_name in names and target_name in names:
            payload.append(
                {
                    "source_name": source_name,
                    "target_name": target_name,
                    "stereotype_slug": edge_slug,
                    "confidence": 0.85,
                }
            )
    return json.dumps(payload)


def _parse_element_names_from_prompt(prompt: str) -> set[str]:
    """Extract element name list embedded as JSON in bootstrap inference prompts."""
    marker = "Elements:"
    if marker not in prompt:
        return set()
    tail = prompt.split(marker, 1)[1].strip()
    try:
        data = json.loads(tail)
    except json.JSONDecodeError:
        return set()
    names: set[str] = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                names.add(item)
            elif isinstance(item, dict) and item.get("name"):
                names.add(str(item["name"]))
    return names
