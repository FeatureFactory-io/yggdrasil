"""
OllamaClient: LLM adapter for local Ollama models (SAO.md §17.3).

Requires Ollama running locally (``make up-desktop``).
Default model: ``qwen3:14b`` (configurable via LLM_OLLAMA_MODEL env).

Not used in unit/integration tests — use ScriptedLLM for those.
"""

from __future__ import annotations

import logging
import os

import httpx

from yggdrasil.llm.base import LLMError, LLMMessage, LLMResponse
from yggdrasil.llm.structured import normalize_llm_text

logger = logging.getLogger("yggdrasil.llm.ollama")

_PREVIEW_CHARS = 1200
_DEFAULT_MODEL = "qwen3:14b"
_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))
_DEFAULT_MAX_TOKENS = int(os.getenv("RATATOSK_LLM_MAX_TOKENS", "8000"))


class OllamaClient:
    """
    Adapter for Ollama local LLM server using the /api/chat endpoint.

    :Example:

    >>> client = OllamaClient(model="qwen3:14b")
    >>> resp = client.complete([LLMMessage(role="user", content="hello")])
    >>> resp.content
    'Hello! How can I help?'
    """

    def __init__(
        self,
        model: str = "",
        base_url: str = "",
    ) -> None:
        """
        :param model: Ollama model tag. Defaults to LLM_OLLAMA_MODEL env or qwen3:14b.
        :param base_url: Ollama server URL. Defaults to OLLAMA_BASE_URL env or localhost:11434.
        """
        self.model_id = model or os.getenv("LLM_OLLAMA_MODEL", _DEFAULT_MODEL)
        self._base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or os.getenv("LLM_OLLAMA_URL")
            or _DEFAULT_BASE_URL
        ).rstrip("/")
        logger.info(
            "OllamaClient: initialised | model=%s base_url=%s",
            self.model_id,
            self._base_url,
        )

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Call Ollama /api/chat and return a structured response.

        :param messages: Conversation history. Minimum: one user message.
        :param system: System prompt. Example: "You are Munin, an architecture AI."
        :param max_tokens: Max tokens in response. Example: 8000
        :param temperature: Sampling temperature. Example: 0.2
        :return: LLMResponse with content, model, usage.
        :raises LLMError: On connection failure, timeout, or non-200 response.
        """
        payload = self._build_payload(messages, system, max_tokens, temperature)
        url = f"{self._base_url}/api/chat"
        user_content = str(messages[-1].content if messages else "")
        logger.info(
            "OllamaClient.complete | entry model=%s messages=%s max_tokens=%s temperature=%s",
            self.model_id,
            len(messages),
            max_tokens,
            temperature,
        )
        if system:
            logger.info(
                "OllamaClient.complete | request.system preview=%s",
                self._preview(system),
            )
        logger.info(
            "OllamaClient.complete | request.user chars=%s preview=%s",
            len(user_content),
            self._preview(user_content),
        )
        try:
            with httpx.Client(timeout=_DEFAULT_TIMEOUT) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                raw = response.json()
        except httpx.HTTPError as exc:
            msg = f"Ollama request failed: {exc}"
            logger.error(
                "OllamaClient.complete | error model=%s url=%s messages=%s system_chars=%s user_chars=%s | %s",
                self.model_id,
                url,
                len(messages),
                len(system),
                len(user_content),
                msg,
            )
            raise LLMError(msg) from exc
        result = self._parse_response(raw)
        logger.info(
            "OllamaClient.complete | result model=%s content_chars=%s thinking_chars=%s usage=%s stop=%s preview=%s",
            result.model,
            len(result.content),
            len(result.thinking),
            result.usage,
            result.stop_reason,
            self._preview(result.content),
        )
        if result.thinking:
            logger.debug(
                "OllamaClient.complete | thinking preview=%s",
                self._preview(result.thinking),
            )
        return result

    @staticmethod
    def _preview(text: str, limit: int = _PREVIEW_CHARS) -> str:
        """Collapse newlines for single-line log previews."""
        collapsed = text.replace("\n", "\\n")
        if len(collapsed) <= limit:
            return collapsed
        return f"{collapsed[:limit]}…({len(text)} chars total)"

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Build the JSON payload for /api/chat."""
        ollama_messages: list[dict[str, str]] = []
        if system:
            ollama_messages.append({"role": "system", "content": system})
        for msg in messages:
            ollama_messages.append({"role": msg.role, "content": msg.content})
        return {
            "model": self.model_id,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
            },
        }

    def _parse_response(self, raw: dict) -> LLMResponse:
        """Parse Ollama /api/chat response JSON into LLMResponse."""
        message = raw.get("message") or {}
        thinking = str(message.get("thinking") or "")
        raw_content = str(message.get("content") or "")
        content = normalize_llm_text(raw_content)
        usage: dict[str, int] = {}
        if raw.get("prompt_eval_count") is not None:
            usage["input"] = int(raw["prompt_eval_count"])
        if raw.get("eval_count") is not None:
            usage["output"] = int(raw["eval_count"])
        logger.info(
            "OllamaClient._parse_response | raw_content_chars=%s thinking_field_chars=%s content_chars=%s",
            len(raw_content),
            len(thinking),
            len(content),
        )
        return LLMResponse(
            content=content,
            model=str(raw.get("model") or self.model_id),
            usage=usage,
            stop_reason="end_turn" if raw.get("done") else "unknown",
            thinking=thinking,
        )
