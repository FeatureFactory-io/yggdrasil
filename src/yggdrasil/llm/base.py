"""
LLM Port: protocol + in-process adapters (SAO.md §17.3 — LLM Port module).

``BaseLLM`` is the protocol all LLM clients implement.
``ScriptedLLM`` replays pre-recorded responses — used in integration tests
so no real LLM call is made (SAO.md §5 — test strategy).

Dependency rules: llm.base has no inbound imports from other Yggdrasil apps.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger("yggdrasil.llm")


class LLMError(Exception):
    """Raised when an LLM call fails or a request/response is invalid."""


@dataclass
class LLMMessage:
    """A single message in a conversation with an LLM.

    :param role: One of "system", "user", "assistant". Example: "user"
    :param content: Message text. Example: "What is the owner of Payment API?"
    """

    role: str
    content: str


@dataclass(frozen=True, slots=True)
class LLMStructuredOutput:
    """Strict JSON schema requested from a provider that supports it."""

    name: str
    schema: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Validate and deeply freeze the JSON schema snapshot."""
        if not self.name.strip():
            raise LLMError("Structured output name must not be empty")
        if not isinstance(self.schema, Mapping) or not self.schema:
            raise LLMError("Structured output schema must be a non-empty mapping")
        object.__setattr__(self, "schema", _freeze_json_value(self.schema))

    def as_json_schema(self) -> dict[str, Any]:
        """Return an independent mutable schema suitable for an SDK payload."""
        schema = _thaw_json_value(self.schema)
        if not isinstance(schema, dict):
            raise AssertionError("Frozen structured output schema must be a mapping")
        return schema


def _freeze_json_value(value: Any) -> Any:
    """Create an immutable recursive snapshot of a JSON-compatible value."""
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise LLMError("Structured output schema keys must be strings")
            frozen[key] = _freeze_json_value(nested_value)
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise LLMError("Structured output schema numbers must be finite")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise LLMError("Structured output schema must contain JSON-compatible values")


def _thaw_json_value(value: Any) -> Any:
    """Materialize an immutable JSON snapshot for an outbound SDK request."""
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(nested_value) for key, nested_value in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class LLMRequestOptions:
    """Optional provider capabilities for one LLM request."""

    structured_output: LLMStructuredOutput | None = None
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        """Reject unsupported reasoning levels before a network call."""
        if self.reasoning_effort is not None and self.reasoning_effort not in {
            "minimal",
            "low",
            "medium",
            "high",
        }:
            raise LLMError(f"Unsupported reasoning effort: {self.reasoning_effort!r}")

    @property
    def is_empty(self) -> bool:
        """Return whether this options object requests no optional capability."""
        return self.structured_output is None and self.reasoning_effort is None


def reject_unsupported_options(
    options: LLMRequestOptions | None,
    *,
    provider: str,
) -> None:
    """Reject OpenAI-only options on providers that cannot honor them."""
    if options is not None and not options.is_empty:
        raise LLMError(f"{provider} provider does not support requested LLM options")


@dataclass
class LLMResponse:
    """The structured response from a single LLM call.

    :param content: Answer text for downstream parsing (thinking stripped).
    :param model: Model identifier string. Example: "qwen2.5-coder:7b"
    :param usage: Token counts dict[str, Any]. Example: {"input": 120, "output": 45}
    :param stop_reason: Why generation stopped. Example: "end_turn"
    :param thinking: Optional reasoning trace when provider exposes it separately.
    """

    content: str
    model: str = ""
    usage: dict[str, Any] = field(default_factory=dict[str, Any])
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
        *,
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        """
        Send messages to the LLM and return a single response.

        :param messages: Conversation history. At minimum one user message.
        :param system: System prompt prepended before messages. Example: "You are Munin..."
        :param max_tokens: Maximum response length in tokens. Example: 1024
        :param temperature: Sampling temperature 0.0-1.0. Example: 0.2
        :param options: Optional structured-output/reasoning capabilities.
        :return: LLMResponse with content, model, usage, stop_reason.
        :raises LLMError: If the API call fails or times out.
        """
        ...


class ScriptedLLM:
    """
    Replays pre-recorded responses in order — for integration tests only.

    Tests construct a ScriptedLLM with a list[Any] of response strings.
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
        :raises ValueError: If responses list[Any] is empty.
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
        *,
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        """
        Return the next scripted response.

        :param messages: Ignored — responses are replayed in order.
        :param system: Ignored.
        :param max_tokens: Ignored.
        :param temperature: Ignored.
        :param options: Must be empty or omitted.
        :return: LLMResponse with the next scripted content.
        :raises LLMError: If all responses have been consumed.
        """
        reject_unsupported_options(options, provider="Scripted")
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
