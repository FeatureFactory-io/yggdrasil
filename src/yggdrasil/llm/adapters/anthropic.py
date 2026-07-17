"""
AnthropicClient: LLM adapter for Anthropic Claude API (SAO.md §17.3).

Requires ANTHROPIC_API_KEY env var. Used in production (cloud) environments.
Default model: claude-3-5-haiku-20241022 (fastest, cheapest for Munin planning).
"""

from __future__ import annotations

import logging
import os

from yggdrasil.llm.base import LLMError, LLMMessage, LLMResponse

logger = logging.getLogger("yggdrasil.llm.anthropic")

_DEFAULT_MODEL = "claude-3-5-haiku-20241022"


class AnthropicClient:
    """
    Adapter for Anthropic Messages API (/v1/messages).

    :Example:

    >>> client = AnthropicClient(model="claude-3-5-haiku-20241022")
    >>> resp = client.complete([LLMMessage(role="user", content="hello")])
    """

    def __init__(self, model: str = "", api_key: str = "") -> None:
        """
        :param model: Claude model string. Defaults to LLM_ANTHROPIC_MODEL env.
        :param api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env.
        :raises LLMError: If api_key is not set.
        """
        self.model_id = model or os.getenv("LLM_ANTHROPIC_MODEL", _DEFAULT_MODEL)
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self._api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set — cannot initialise AnthropicClient")
        logger.info("AnthropicClient: initialised | model=%s", self.model_id)

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Call Anthropic /v1/messages and return a structured response.

        :param messages: Conversation history.
        :param system: System prompt prepended before messages.
        :param max_tokens: Max tokens. Example: 1024
        :param temperature: Sampling temperature. Example: 0.2
        :return: LLMResponse with content, model, usage, stop_reason.
        :raises LLMError: On API error, rate limit, or invalid key.
        """
        raise NotImplementedError()

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Build the JSON payload for /v1/messages."""
        raise NotImplementedError()

    def _parse_response(self, raw: dict) -> LLMResponse:
        """Parse Anthropic Messages API response into LLMResponse."""
        raise NotImplementedError()
