"""LLM provider abstraction — shared by web chat and Ratatosk."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
from django.conf import settings

logger = logging.getLogger("yggdrasil.tokens")


@dataclass
class LLMResponse:
    content: str
    tokens_in: int
    tokens_out: int


class LLM(ABC):
    """Abstract LLM provider."""

    def __init__(self, base_url: str, model: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        ...


class QwenLLM(LLM):
    """OpenAI-compatible local endpoint (e.g. Ollama, vLLM)."""

    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages}
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        logger.info(
            "provider=qwen model=%s tokens_in=%d tokens_out=%d",
            self.model, tokens_in, tokens_out,
        )
        return LLMResponse(content=content, tokens_in=tokens_in, tokens_out=tokens_out)


class AnthropicLLM(LLM):
    """Anthropic Messages API."""

    def complete(self, prompt: str, system: str = "") -> LLMResponse:
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(f"{self.base_url}/v1/messages", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        content = data["content"][0]["text"]
        usage = data.get("usage", {})
        tokens_in = usage.get("input_tokens", 0)
        tokens_out = usage.get("output_tokens", 0)
        logger.info(
            "provider=anthropic model=%s tokens_in=%d tokens_out=%d",
            self.model, tokens_in, tokens_out,
        )
        return LLMResponse(content=content, tokens_in=tokens_in, tokens_out=tokens_out)


def get_llm() -> LLM:
    """Factory from Django settings."""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "anthropic":
        return AnthropicLLM(
            base_url=settings.LLM_BASE_URL,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
        )
    return QwenLLM(
        base_url=settings.LLM_BASE_URL,
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
    )
