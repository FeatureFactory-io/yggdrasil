"""
OllamaClient: LLM adapter for local Ollama models (SAO.md §17.3).

Requires Ollama running locally (``make up-desktop``).
Default model: ``qwen3:14b`` (configurable via LLM_OLLAMA_MODEL env).

Not used in unit/integration tests — use ScriptedLLM for those.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from yggdrasil.llm.base import LLMMessage, LLMResponse

logger = logging.getLogger("yggdrasil.llm.ollama")

_DEFAULT_MODEL = "qwen3:14b"
_DEFAULT_BASE_URL = "http://localhost:11434"


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
        )
        logger.info(
            "OllamaClient: initialised | model=%s base_url=%s",
            self.model_id,
            self._base_url,
        )

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Call Ollama /api/chat and return a structured response.

        :param messages: Conversation history. Minimum: one user message.
        :param system: System prompt. Example: "You are Munin, an architecture AI."
        :param max_tokens: Max tokens in response. Example: 1024
        :param temperature: Sampling temperature. Example: 0.2
        :return: LLMResponse with content, model, usage.
        :raises LLMError: On connection failure, timeout, or non-200 response.
        """
        raise NotImplementedError()

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Build the JSON payload for /api/chat."""
        raise NotImplementedError()

    def _parse_response(self, raw: dict) -> LLMResponse:
        """Parse Ollama /api/chat response JSON into LLMResponse."""
        raise NotImplementedError()
