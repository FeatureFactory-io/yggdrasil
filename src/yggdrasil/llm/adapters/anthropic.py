"""
AnthropicClient: LLM adapter for Anthropic Claude API (SAO.md §17.3).

Requires ANTHROPIC_API_KEY env var. Used in production (cloud) environments.
Default model: claude-haiku-4-5-20251001 (fastest, cheapest for Ratatosk field tier).
"""

from __future__ import annotations

import logging
import os

from yggdrasil.llm.base import LLMError, LLMMessage, LLMResponse
from yggdrasil.llm.structured import normalize_llm_text

logger = logging.getLogger("yggdrasil.llm.anthropic")

_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_TOKENS = int(os.getenv("RATATOSK_LLM_MAX_TOKENS", "8000"))


class AnthropicClient:
    """
    Adapter for Anthropic Messages API (/v1/messages).

    :Example:

    >>> client = AnthropicClient(model="claude-3-5-haiku-20241022", api_key="sk-test")
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
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Call Anthropic /v1/messages and return a structured response.

        :param messages: Conversation history.
        :param system: System prompt prepended before messages.
        :param max_tokens: Max tokens. Example: 8000
        :param temperature: Sampling temperature. Example: 0.2
        :return: LLMResponse with content, model, usage, stop_reason.
        :raises LLMError: On API error, rate limit, or invalid key.
        """
        payload = self._build_payload(messages, system, max_tokens, temperature)
        logger.info(
            "AnthropicClient.complete | entry model=%s messages=%s max_tokens=%s",
            self.model_id,
            len(messages),
            max_tokens,
        )
        try:
            raw = self._call_sdk(payload)
        except Exception as exc:
            msg = f"Anthropic request failed for model={self.model_id}: {exc}"
            logger.error(
                "AnthropicClient.complete | error model=%s class=%s",
                self.model_id,
                type(exc).__name__,
            )
            raise LLMError(msg) from exc
        result = self._parse_response(raw)
        logger.info(
            "AnthropicClient.complete | result model=%s content_chars=%s thinking_chars=%s usage=%s stop=%s",
            result.model,
            len(result.content),
            len(result.thinking),
            result.usage,
            result.stop_reason,
        )
        return result

    def _call_sdk(self, payload: dict) -> dict:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(**payload)
        if hasattr(response, "model_dump"):
            return response.model_dump()
        return dict(response)

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system: str,
        max_tokens: int,
        temperature: float,
    ) -> dict:
        """Build the JSON payload for /v1/messages."""
        payload: dict = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": msg.role, "content": msg.content} for msg in messages],
        }
        if system:
            payload["system"] = system
        return payload

    def _parse_response(self, raw: dict) -> LLMResponse:
        """Parse Anthropic Messages API response into LLMResponse."""
        thinking, text = self._extract_text_blocks(raw.get("content") or [])
        content = normalize_llm_text(text)
        usage_raw = raw.get("usage") or {}
        usage: dict[str, int] = {}
        if usage_raw.get("input_tokens") is not None:
            usage["input"] = int(usage_raw["input_tokens"])
        if usage_raw.get("output_tokens") is not None:
            usage["output"] = int(usage_raw["output_tokens"])
        if thinking:
            logger.debug(
                "AnthropicClient._parse_response | thinking_chars=%s stripped from content",
                len(thinking),
            )
        return LLMResponse(
            content=content,
            model=str(raw.get("model") or self.model_id),
            usage=usage,
            stop_reason=str(raw.get("stop_reason") or "end_turn"),
            thinking=thinking,
        )

    @staticmethod
    def _extract_text_blocks(blocks: list) -> tuple[str, str]:
        """Return (thinking_text, answer_text) from Anthropic content blocks."""
        thinking_parts: list[str] = []
        text_parts: list[str] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "thinking":
                thinking_parts.append(str(block.get("thinking") or ""))
            elif block_type == "text":
                text_parts.append(str(block.get("text") or ""))
        return "".join(thinking_parts), "".join(text_parts)
