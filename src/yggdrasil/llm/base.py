"""
LLM Port: protocol + in-process adapters (SAO.md §17.3 — LLM Port module).

``BaseLLM`` is the protocol all LLM clients implement.
``ScriptedLLM`` replays pre-recorded responses — used in integration tests
so no real LLM call is made (SAO.md §5 — test strategy).

Dependency rules: llm.base has no inbound imports from other Yggdrasil apps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

logger = logging.getLogger("yggdrasil.llm")


@dataclass
class LLMMessage:
    """A single message in a conversation with an LLM.

    :param role: One of "system", "user", "assistant". Example: "user"
    :param content: Message text. Example: "What is the owner of Payment API?"
    """

    role: str
    content: str


@dataclass
class LLMResponse:
    """The structured response from a single LLM call.

    :param content: Answer text for downstream parsing (thinking stripped).
    :param model: Model identifier string. Example: "qwen2.5-coder:7b"
    :param usage: Token counts dict. Example: {"input": 120, "output": 45}
    :param stop_reason: Why generation stopped. Example: "end_turn"
    :param thinking: Optional reasoning trace when provider exposes it separately.
    """

    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)
    stop_reason: str = "end_turn"
    thinking: str = ""


@runtime_checkable
class BaseLLM(Protocol):
    """
    Protocol that all LLM adapters must satisfy.

    Any class implementing ``complete`` and ``model_id`` is a valid BaseLLM.
    This enables static duck-typing while keeping adapters decoupled.

    :Example:

    >>> class MyAdapter:
    ...     model_id = "my-model"
    ...     def complete(self, messages, system="", max_tokens=1024, temperature=0.2):
    ...         return LLMResponse(content="ok", model=self.model_id)
    >>> isinstance(MyAdapter(), BaseLLM)
    True
    """

    model_id: str

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Send messages to the LLM and return a single response.

        :param messages: Conversation history. At minimum one user message.
        :param system: System prompt prepended before messages. Example: "You are Munin..."
        :param max_tokens: Maximum response length in tokens. Example: 1024
        :param temperature: Sampling temperature 0.0-1.0. Example: 0.2
        :return: LLMResponse with content, model, usage, stop_reason.
        :raises LLMError: If the API call fails or times out.
        """
        ...


class LLMError(Exception):
    """Raised when an LLM call fails (timeout, API error, invalid response)."""


class ScriptedLLM:
    """
    Replays pre-recorded responses in order — for integration tests only.

    Tests construct a ScriptedLLM with a list of response strings.
    Each call to ``complete`` pops the next response; raises if exhausted.

    Never use in production — inject via LLM_PROVIDER=scripted in test settings.

    :Example:

    >>> llm = ScriptedLLM(responses=["payments-team", "6 elements"])
    >>> llm.complete([LLMMessage(role="user", content="who owns Payment API?")]).content
    'payments-team'
    >>> llm.complete([LLMMessage(role="user", content="how many elements?")]).content
    '6 elements'
    """

    model_id = "scripted"

    def __init__(self, responses: list[str]) -> None:
        """
        :param responses: Pre-recorded response strings in call order.
        :raises ValueError: If responses list is empty.
        """
        if not responses:
            raise ValueError("ScriptedLLM requires at least one response")
        self._responses = list(responses)
        self._index = 0

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """
        Return the next scripted response.

        :param messages: Ignored — responses are replayed in order.
        :param system: Ignored.
        :param max_tokens: Ignored.
        :param temperature: Ignored.
        :return: LLMResponse with the next scripted content.
        :raises LLMError: If all responses have been consumed.
        """
        logger.debug(
            "ScriptedLLM.complete: call %d | messages=%d",
            self._index,
            len(messages),
        )
        if self._index >= len(self._responses):
            raise LLMError(f"ScriptedLLM exhausted after {len(self._responses)} calls")
        content = self._responses[self._index]
        self._index += 1
        logger.debug("ScriptedLLM.complete: returning response %d", self._index)
        return LLMResponse(content=content, model=self.model_id)
