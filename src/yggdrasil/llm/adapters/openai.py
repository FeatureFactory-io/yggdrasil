"""OpenAI Responses API adapter for the provider-neutral LLM port."""

from __future__ import annotations

import logging
import os
import random
import time
from collections.abc import Callable, Mapping
from typing import Any

from yggdrasil.llm.base import LLMError, LLMMessage, LLMRequestOptions, LLMResponse
from yggdrasil.llm.provider_config import openai_endpoint_origin, resolve_openai_base_url
from yggdrasil.llm.structured import normalize_llm_text

logger = logging.getLogger("yggdrasil.llm.openai")

_DEFAULT_MODEL = "gpt-5.6-terra"
_DEFAULT_TIMEOUT = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
_DEFAULT_MAX_TOKENS = int(os.getenv("RATATOSK_LLM_MAX_TOKENS", "8000"))
_MAX_ATTEMPTS = 3
_BACKOFF_SECONDS = 1.0
_TRANSIENT_EXCEPTION_NAMES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "InternalServerError",
        "RateLimitError",
    }
)
_TRANSIENT_STATUS_CODES = frozenset({408, 409, 429, 500, 502, 503, 504})
_VALID_ROLES = frozenset({"system", "user", "assistant", "developer"})


class OpenAIClient:
    """Call the OpenAI Responses API and return normalized LLM responses.

    :param model: OpenAI model ID. Defaults to ``LLM_OPENAI_MODEL``.
    :param api_key: OpenAI API key. Defaults to ``OPENAI_API_KEY``.
    :param base_url: Optional Responses API base URL. Example: ``http://127.0.0.1:1234/v1``.
    :param sdk_client: Optional injected SDK client for deterministic tests.
    :param sleep_fn: Optional sleep function for deterministic retry tests.
    :param random_fn: Optional jitter source for deterministic retry tests.
    :raises LLMError: If configuration is invalid or the SDK is unavailable.
    """

    model_id: str

    def __init__(
        self,
        model: str = "",
        api_key: str = "",
        *,
        base_url: str | None = None,
        sdk_client: Any | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        random_fn: Callable[[], float] | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self.model_id = (model or os.getenv("LLM_OPENAI_MODEL", _DEFAULT_MODEL)).strip()
        self._api_key = (api_key or os.getenv("OPENAI_API_KEY", "")).strip()
        self._timeout = self._validate_timeout(timeout)
        if not self.model_id:
            raise LLMError("OpenAI model must not be empty")
        if not self._api_key:
            raise LLMError("OPENAI_API_KEY is not set - cannot initialise OpenAIClient")
        try:
            self._base_url = resolve_openai_base_url(base_url)
        except ValueError as exc:
            raise LLMError(f"Invalid OPENAI_BASE_URL: {exc}") from exc
        self._sleep: Callable[[float], None] = sleep_fn or time.sleep
        self._random: Callable[[], float] = random_fn or random.random
        self._client = sdk_client or self._create_sdk_client()
        logger.info(
            "OpenAIClient.__init__ | exit | model=%s endpoint_mode=%s endpoint_origin=%s",
            self.model_id,
            "custom" if self._base_url else "official",
            openai_endpoint_origin(self._base_url),
        )

    def complete(
        self,
        messages: list[LLMMessage],
        system: str = "",
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        temperature: float = 0.2,
        *,
        options: LLMRequestOptions | None = None,
    ) -> LLMResponse:
        """Call Responses API with bounded retries and normalize its result."""
        payload = self._build_payload(messages, system, max_tokens, temperature, options)
        raw = self._request_with_retries(payload)
        result = self._parse_response(raw)
        logger.info(
            "OpenAIClient.complete | result model=%s content_chars=%s usage=%s stop=%s",
            result.model,
            len(result.content),
            result.usage,
            result.stop_reason,
        )
        return result

    def _build_payload(
        self,
        messages: list[LLMMessage],
        system: str,
        max_tokens: int,
        temperature: float,
        options: LLMRequestOptions | None,
    ) -> dict[str, Any]:
        """Validate request inputs and build a Responses API payload."""
        self._validate_messages(messages)
        self._validate_generation(max_tokens, temperature)
        input_items = self._build_input_items(messages, system)
        payload: dict[str, Any] = {
            "model": self.model_id,
            "input": input_items,
            "max_output_tokens": max_tokens,
        }
        if options and options.reasoning_effort:
            payload["reasoning"] = {"effort": options.reasoning_effort}
        else:
            payload["temperature"] = temperature
        if options and options.structured_output:
            structured = options.structured_output
            payload["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": structured.name,
                    "schema": dict(structured.schema),
                    "strict": True,
                }
            }
        return payload

    @staticmethod
    def _build_input_items(messages: list[LLMMessage], system: str) -> list[dict[str, str]]:
        """Map repository messages to Responses API input items."""
        items: list[dict[str, str]] = []
        if system.strip():
            items.append({"role": "developer", "content": system})
        for message in messages:
            role = "developer" if message.role == "system" else message.role
            items.append({"role": role, "content": message.content})
        return items

    @staticmethod
    def _validate_messages(messages: list[LLMMessage]) -> None:
        """Reject empty or unsupported message inputs before network access."""
        if not messages:
            raise LLMError("OpenAI request requires at least one message")
        for message in messages:
            if message.role not in _VALID_ROLES:
                raise LLMError(f"Invalid OpenAI message role: {message.role!r}")
            if not message.content.strip():
                raise LLMError("OpenAI messages must not contain empty content")

    @staticmethod
    def _validate_generation(max_tokens: int, temperature: float) -> None:
        """Validate generation controls without silently clamping values."""
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens <= 0:
            raise LLMError("OpenAI max_tokens must be a positive integer")
        if (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
            or not 0.0 <= temperature <= 1.0
        ):
            raise LLMError("OpenAI temperature must be between 0.0 and 1.0")

    def _request_with_retries(self, payload: dict[str, Any]) -> Any:
        """Execute the request with bounded retries for transient failures."""
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            logger.info(
                "OpenAIClient.complete | attempt=%s model=%s fields=%s",
                attempt,
                self.model_id,
                sorted(payload),
            )
            try:
                return self._client.responses.create(**payload)
            except Exception as exc:
                if not self._is_transient(exc) or attempt == _MAX_ATTEMPTS:
                    self._log_failure(exc, attempt)
                    raise self._as_llm_error(exc) from exc
                delay = self._backoff_seconds(attempt)
                self._log_failure(exc, attempt, retry_delay=delay)
                self._sleep(delay)
        raise AssertionError("OpenAI retry loop exited without result")

    def _parse_response(self, raw: Any) -> LLMResponse:
        """Extract public text and usage from a Responses API result."""
        content = normalize_llm_text(self._extract_output_text(raw))
        if not content:
            raise LLMError("LLMError identifying malformed or incomplete OpenAI response")
        usage = self._extract_usage(raw)
        stop_reason = self._extract_stop_reason(raw)
        return LLMResponse(
            content=content,
            model=str(self._value(raw, "model") or self.model_id),
            usage=usage,
            stop_reason=stop_reason,
            thinking="",
        )

    @classmethod
    def _extract_output_text(cls, raw: Any) -> str:
        """Extract output_text without exposing reasoning items."""
        direct = cls._value(raw, "output_text")
        if isinstance(direct, str) and direct.strip():
            return direct
        output = cls._value(raw, "output") or []
        parts: list[str] = []
        for item in output if isinstance(output, list) else []:
            for part in cls._value(item, "content") or []:
                if cls._value(part, "type") == "output_text":
                    text = cls._value(part, "text")
                    if isinstance(text, str):
                        parts.append(text)
        return "".join(parts)

    @classmethod
    def _extract_usage(cls, raw: Any) -> dict[str, int]:
        """Map provider usage fields to the repository usage vocabulary."""
        usage_raw = cls._value(raw, "usage") or {}
        usage: dict[str, int] = {}
        for source, target in (
            ("input_tokens", "input"),
            ("output_tokens", "output"),
            ("total_tokens", "total"),
        ):
            value = cls._value(usage_raw, source)
            if value is not None:
                usage[target] = int(value)
        details = cls._value(usage_raw, "output_tokens_details") or {}
        reasoning = cls._value(details, "reasoning_tokens")
        if reasoning is not None:
            usage["reasoning"] = int(reasoning)
        return usage

    @classmethod
    def _extract_stop_reason(cls, raw: Any) -> str:
        """Return the provider completion status or incomplete reason."""
        status = cls._value(raw, "status")
        if isinstance(status, str) and status:
            return status
        details = cls._value(raw, "incomplete_details") or {}
        reason = cls._value(details, "reason")
        return str(reason or "unknown")

    @staticmethod
    def _value(raw: Any, key: str) -> Any:
        """Read a field from SDK objects, mappings, or model-dumpable objects."""
        if isinstance(raw, Mapping):
            return raw.get(key)
        value = getattr(raw, key, None)
        if value is not None:
            return value
        model_dump = getattr(raw, "model_dump", None)
        if callable(model_dump):
            dumped = model_dump()
            if isinstance(dumped, Mapping):
                return dumped.get(key)
        return None

    def _create_sdk_client(self) -> Any:
        """Construct the official SDK client with SDK retries disabled."""
        try:
            import openai
        except ImportError as exc:
            raise LLMError("OpenAI SDK is unavailable; install the openai dependency") from exc
        try:
            client_kwargs: dict[str, Any] = {
                "api_key": self._api_key,
                "max_retries": 0,
                "timeout": self._timeout,
            }
            if self._base_url is not None:
                client_kwargs["base_url"] = self._base_url
            return openai.OpenAI(
                **client_kwargs,
            )
        except Exception as exc:
            raise LLMError("OpenAI SDK client initialization failed") from exc

    @staticmethod
    def _validate_timeout(timeout: float) -> float:
        """Validate the adapter timeout without accepting an unsafe value."""
        if timeout <= 0:
            raise LLMError("OpenAI timeout must be positive")
        return float(timeout)

    def _is_transient(self, exc: Exception) -> bool:
        """Classify only documented transport/rate/server failures as retryable."""
        if type(exc).__name__ in _TRANSIENT_EXCEPTION_NAMES:
            return True
        return getattr(exc, "status_code", None) in _TRANSIENT_STATUS_CODES

    def _backoff_seconds(self, attempt: int) -> float:
        """Calculate bounded exponential backoff with jitter."""
        random_value = float(self._random())
        jitter = 0.5 + min(max(random_value, 0.0), 1.0)
        return float(_BACKOFF_SECONDS * (2 ** (attempt - 1)) * jitter)

    def _log_failure(self, exc: Exception, attempt: int, retry_delay: float | None = None) -> None:
        """Log failure metadata without provider payloads or credentials."""
        logger.warning(
            "OpenAIClient.complete | failure model=%s attempt=%s error=%s status=%s request_id=%s retry_delay=%s",
            self.model_id,
            attempt,
            type(exc).__name__,
            getattr(exc, "status_code", None),
            getattr(exc, "request_id", None) or getattr(exc, "_request_id", None),
            retry_delay,
        )

    def _as_llm_error(self, exc: Exception) -> LLMError:
        """Convert an SDK exception to a message that cannot leak its payload."""
        return LLMError(f"OpenAI request failed for model={self.model_id}: {type(exc).__name__}")
