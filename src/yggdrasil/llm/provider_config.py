"""Shared provider model and endpoint configuration helpers."""

from __future__ import annotations

import ipaddress
from types import MappingProxyType
from typing import TYPE_CHECKING, Any
from urllib.parse import SplitResult, urlsplit, urlunsplit

if TYPE_CHECKING:
    from collections.abc import Mapping

DEFAULT_ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_OLLAMA_MODEL = "qwen3:14b"
DEFAULT_OPENAI_MODEL = "gpt-5.6-terra"
DEFAULT_OPENAI_FAST_MODEL = "gpt-5.6-luna"
DEFAULT_OPENAI_QUALITY_MODEL = "gpt-5.6-sol"

MODEL_ALIASES: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "anthropic": MappingProxyType(
            {
                "haiku": DEFAULT_ANTHROPIC_MODEL,
                "sonnet5": "claude-sonnet-4-5-20250929",
            }
        ),
        "ollama": MappingProxyType({}),
        "openai": MappingProxyType(
            {
                "openai_fast": DEFAULT_OPENAI_FAST_MODEL,
                "openai_quality": DEFAULT_OPENAI_QUALITY_MODEL,
            }
        ),
    }
)


def resolve_model_id(provider: str, raw_model: str, *, default_model: str) -> str:
    """
    Resolve a provider model alias or pass through an explicit model identifier.

    :param provider: selected provider as str. Example: "openai".
    :param raw_model: operator model setting as str. Example: "openai_fast".
    :param default_model: provider default model identifier as str. Example: "gpt-5.6-terra".
    :return: resolved model identifier as str. Example: "gpt-5.6-luna".
    :raises ValueError: if a known foreign alias or invalid Anthropic identifier is selected.
    """
    normalized_provider = provider.strip().lower()
    cleaned_model = _clean_model_id(raw_model)
    if not cleaned_model:
        return default_model

    aliases = MODEL_ALIASES.get(normalized_provider, MappingProxyType({}))
    if cleaned_model in aliases:
        return aliases[cleaned_model]
    if normalized_provider == "openai" and _is_foreign_alias(cleaned_model, normalized_provider):
        raise ValueError(f"Unknown model alias {cleaned_model!r} for provider openai")
    if normalized_provider == "anthropic" and not cleaned_model.startswith("claude"):
        raise ValueError(f"Unknown model alias {cleaned_model!r} for provider anthropic")
    return cleaned_model


def resolve_openai_base_url(raw_base_url: str | None) -> str | None:
    """
    Validate and normalize an optional OpenAI-compatible Responses API base URL.

    :param raw_base_url: endpoint setting as str or None. Example: "http://127.0.0.1:1234/v1".
    :return: normalized endpoint as str or None. Example: "http://127.0.0.1:1234/v1".
    :raises ValueError: if the endpoint is malformed or unsafe for credential transport.
    """
    cleaned_url = str(raw_base_url or "").strip()
    if not cleaned_url:
        return None
    if any(character.isspace() or ord(character) < 32 for character in cleaned_url):
        raise ValueError("OPENAI_BASE_URL must be a valid HTTP(S) URL")

    parsed = urlsplit(cleaned_url)
    _validate_openai_base_url(parsed)
    normalized_path = parsed.path.rstrip("/")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, normalized_path, "", ""))


def openai_endpoint_origin(base_url: str | None) -> str:
    """
    Return a safe endpoint origin label for logs.

    :param base_url: validated endpoint as str or None. Example: "https://gateway.example/v1".
    :return: safe origin label as str. Example: "https://gateway.example".
    """
    if base_url is None:
        return "official"
    parsed = urlsplit(base_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def build_openai_client(model_id: str, api_key: str, base_url: str | None) -> Any:
    """
    Construct the shared OpenAI-compatible provider adapter.

    :param model_id: resolved model identifier as str. Example: "gpt-5.6-terra".
    :param api_key: provider credential as str. Example: "local-test".
    :param base_url: validated endpoint as str or None. Example: "http://127.0.0.1:1234/v1".
    :return: OpenAI-compatible BaseLLM as Any. Example: OpenAIClient instance.
    :raises LLMError: if OpenAIClient rejects credentials or endpoint configuration.
    """
    from yggdrasil.llm.adapters.openai import OpenAIClient

    return OpenAIClient(model=model_id, api_key=api_key, base_url=base_url)


def _clean_model_id(raw_model: str) -> str:
    """Return a model ID stripped of surrounding whitespace."""
    cleaned_model = str(raw_model or "").strip()
    if any(ord(character) < 32 for character in cleaned_model):
        raise ValueError("Model identifier must not contain control characters")
    return cleaned_model


def _is_foreign_alias(model_id: str, provider: str) -> bool:
    """Return whether a symbolic alias belongs to a different provider."""
    return any(
        model_id in aliases
        for alias_provider, aliases in MODEL_ALIASES.items()
        if alias_provider != provider
    )


def _validate_openai_base_url(parsed: SplitResult) -> None:
    """Validate URL structure and require secure transport away from loopback."""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("OPENAI_BASE_URL must be a valid HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("OPENAI_BASE_URL must not contain credentials, query, or fragment")
    try:
        hostname = parsed.hostname
        _ = parsed.port
    except ValueError as exc:
        raise ValueError("OPENAI_BASE_URL must contain a valid host and port") from exc
    if not hostname:
        raise ValueError("OPENAI_BASE_URL must contain a host")
    if parsed.scheme == "http" and not _is_loopback_host(hostname):
        raise ValueError("OPENAI_BASE_URL must use HTTPS outside loopback")


def _is_loopback_host(hostname: str) -> bool:
    """Return whether a hostname is localhost or an IP loopback address."""
    if hostname.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False
