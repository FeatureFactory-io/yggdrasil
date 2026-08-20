"""Unit tests for the OpenAI Responses API adapter."""

from __future__ import annotations

import logging
from types import SimpleNamespace

import openai
import pytest

from yggdrasil.llm.adapters.openai import OpenAIClient
from yggdrasil.llm.base import (
    LLMError,
    LLMMessage,
    LLMRequestOptions,
    LLMStructuredOutput,
    ScriptedLLM,
)


class RateLimitError(Exception):
    """SDK-shaped transient failure for deterministic retry tests."""

    status_code = 429


class AuthenticationError(Exception):
    """SDK-shaped permanent failure for deterministic error tests."""

    status_code = 401


class PermissionError(Exception):
    """SDK-shaped permanent permission failure."""

    status_code = 403


class ValidationError(Exception):
    """SDK-shaped permanent validation failure."""

    status_code = 400


class APITimeoutError(Exception):
    """SDK-shaped transient timeout failure."""


class APIConnectionError(Exception):
    """SDK-shaped transient connection failure."""


class InternalServerError(Exception):
    """SDK-shaped transient server failure."""

    status_code = 500


class _Responses:
    def __init__(self, results: list[object]) -> None:
        self._results = list(results)
        self.calls: list[dict[str, object]] = []

    def create(self, **payload: object) -> object:
        self.calls.append(payload)
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


class _SDKClient:
    def __init__(self, results: list[object]) -> None:
        self.responses = _Responses(results)


def _response(content: str = "ok") -> SimpleNamespace:
    return SimpleNamespace(
        output_text=content,
        model="gpt-test",
        status="completed",
        usage=SimpleNamespace(
            input_tokens=11,
            output_tokens=7,
            total_tokens=18,
            output_tokens_details=SimpleNamespace(reasoning_tokens=2),
        ),
    )


def _client(
    results: list[object],
    *,
    sleeps: list[float] | None = None,
) -> tuple[OpenAIClient, _SDKClient]:
    sdk = _SDKClient(results)
    client = OpenAIClient(
        model="gpt-test",
        api_key="sk-test",
        sdk_client=sdk,
        sleep_fn=(sleeps.append if sleeps is not None else lambda _delay: None),
        random_fn=lambda: 0.5,
    )
    return client, sdk


def test_openai_payload_maps_system_messages_and_structured_output() -> None:
    """Responses payload preserves messages and strict schema options."""
    client, sdk = _client([_response('```json\n{"ok": true}\n```')])
    options = LLMRequestOptions(
        structured_output=LLMStructuredOutput(
            name="result",
            schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
        )
    )

    result = client.complete(
        [LLMMessage(role="user", content="hello")],
        system="Be concise.",
        max_tokens=512,
        temperature=0.1,
        options=options,
    )

    payload = sdk.responses.calls[0]
    assert result.content == '{"ok": true}'
    assert payload["model"] == "gpt-test"
    assert payload["max_output_tokens"] == 512
    assert payload["input"] == [
        {"role": "developer", "content": "Be concise."},
        {"role": "user", "content": "hello"},
    ]
    assert payload["text"] == {
        "format": {
            "type": "json_schema",
            "name": "result",
            "schema": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
            "strict": True,
        }
    }


def test_openai_structured_schema_is_a_deep_immutable_snapshot() -> None:
    """Nested caller mutations cannot alter an already-validated schema request."""
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
    }
    structured_output = LLMStructuredOutput(name="result", schema=schema)
    options = LLMRequestOptions(structured_output=structured_output)
    schema["properties"]["ok"]["type"] = "string"
    schema["required"].append("changed")

    client, sdk = _client([_response()])
    client.complete([LLMMessage(role="user", content="hello")], options=options)

    assert sdk.responses.calls[0]["text"] == {
        "format": {
            "type": "json_schema",
            "name": "result",
            "schema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}},
                "required": ["ok"],
            },
            "strict": True,
        }
    }
    with pytest.raises(TypeError):
        structured_output.schema["properties"]["ok"]["type"] = "string"


@pytest.mark.parametrize("invalid_number", [float("nan"), float("inf"), float("-inf")])
def test_openai_structured_schema_rejects_non_finite_numbers(invalid_number: float) -> None:
    """Strict JSON schemas reject values that cannot be represented in JSON."""
    with pytest.raises(LLMError, match="finite"):
        LLMStructuredOutput(name="result", schema={"maximum": invalid_number})


def test_openai_reasoning_effort_uses_reasoning_payload_without_temperature() -> None:
    """Reasoning requests use the provider reasoning field explicitly."""
    client, sdk = _client([_response()])
    client.complete(
        [LLMMessage(role="user", content="reason")],
        options=LLMRequestOptions(reasoning_effort="low"),
    )
    payload = sdk.responses.calls[0]
    assert payload["reasoning"] == {"effort": "low"}
    assert "temperature" not in payload


def test_openai_response_maps_usage_and_never_exposes_thinking() -> None:
    """Provider response metadata is normalized and public thinking stays empty."""
    client, _ = _client([_response()])
    result = client.complete([LLMMessage(role="user", content="hello")])
    assert result.model == "gpt-test"
    assert result.usage == {"input": 11, "output": 7, "total": 18, "reasoning": 2}
    assert result.stop_reason == "completed"
    assert result.thinking == ""


def test_openai_response_extracts_output_content_without_output_text() -> None:
    """Responses output items remain supported when the convenience field is absent."""
    raw = SimpleNamespace(
        output_text="",
        model="gpt-test",
        status="completed",
        output=[
            SimpleNamespace(
                content=[SimpleNamespace(type="output_text", text="fallback response text")]
            )
        ],
    )
    client, _ = _client([raw])

    result = client.complete([LLMMessage(role="user", content="hello")])

    assert result.content == "fallback response text"


def test_openai_malformed_usage_is_not_a_successful_response() -> None:
    """Malformed token metadata maps to LLMError rather than leaking a conversion error."""
    raw = _response()
    raw.usage.output_tokens = "unknown"
    client, _ = _client([raw])

    with pytest.raises(LLMError, match="malformed usage"):
        client.complete([LLMMessage(role="user", content="hello")])


def test_openai_missing_key_fails_before_sdk_construction(monkeypatch) -> None:
    """Missing credentials are rejected before any provider call."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(LLMError, match="OPENAI_API_KEY"):
        OpenAIClient(model="gpt-test", api_key="", sdk_client=object())


def test_openai_custom_base_url_is_passed_explicitly_to_sdk(monkeypatch) -> None:
    """A compatible Responses endpoint is explicit rather than SDK-env implicit."""
    constructor_args: dict[str, object] = {}

    class _FakeSDKOpenAI:
        def __init__(self, **kwargs: object) -> None:
            constructor_args.update(kwargs)

    monkeypatch.setattr(openai, "OpenAI", _FakeSDKOpenAI)
    OpenAIClient(
        model="gemma-4-e4b-uncensored-hauhaucs-aggressive",
        api_key="local-test",
        base_url="http://127.0.0.1:1234/v1",
    )
    assert constructor_args["base_url"] == "http://127.0.0.1:1234/v1"
    assert constructor_args["max_retries"] == 0


def test_openai_uses_official_sdk_base_url_when_not_explicit(monkeypatch) -> None:
    """Official routing cannot inherit an unvalidated SDK environment endpoint."""
    monkeypatch.setenv("OPENAI_BASE_URL", "http://example.test/v1")
    client = OpenAIClient(model="gpt-test", api_key="sk-test")
    assert str(client._client.base_url) == "https://api.openai.com/v1/"


@pytest.mark.parametrize("timeout", ["invalid", 0, -1, float("inf"), True])
def test_openai_invalid_timeout_fails_as_configuration_error(timeout: object) -> None:
    """Invalid explicit timeout values never escape the adapter error boundary."""
    with pytest.raises(LLMError, match="timeout"):
        OpenAIClient(model="gpt-test", api_key="sk-test", sdk_client=object(), timeout=timeout)  # type: ignore[arg-type]


def test_openai_invalid_timeout_environment_fails_as_configuration_error(monkeypatch) -> None:
    """Malformed timeout environment data is validated when the client is constructed."""
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "invalid")

    with pytest.raises(LLMError, match="timeout"):
        OpenAIClient(model="gpt-test", api_key="sk-test", sdk_client=object())


def test_openai_invalid_messages_fail_before_request() -> None:
    """Empty messages are an explicit request rejection."""
    client, sdk = _client([_response()])
    with pytest.raises(LLMError, match="at least one message"):
        client.complete([])
    assert sdk.responses.calls == []


def test_openai_malformed_response_is_not_success() -> None:
    """Missing public text maps to LLMError rather than empty success."""
    client, _ = _client([SimpleNamespace(output_text="", status="completed")])
    with pytest.raises(LLMError, match="malformed or incomplete"):
        client.complete([LLMMessage(role="user", content="hello")])


@pytest.mark.parametrize("status", ["incomplete", "failed", "cancelled"])
def test_openai_non_completed_response_is_not_success(status: str) -> None:
    """Partial provider output must not become a downstream success result."""
    client, _ = _client([SimpleNamespace(output_text="partial", status=status)])
    with pytest.raises(LLMError, match="did not complete"):
        client.complete([LLMMessage(role="user", content="hello")])


def test_openai_non_completed_response_is_not_retried() -> None:
    """A successful HTTP response with incomplete generation is never resent."""
    client, sdk = _client(
        [
            SimpleNamespace(output_text="partial", status="incomplete"),
            _response("must remain unused"),
        ]
    )

    with pytest.raises(LLMError, match="did not complete"):
        client.complete([LLMMessage(role="user", content="hello")])

    assert len(sdk.responses.calls) == 1


@pytest.mark.parametrize(
    "failure",
    [PermissionError(), ValidationError()],
    ids=["permission", "validation"],
)
def test_openai_permanent_failures_are_explicit_and_not_retried(failure: Exception) -> None:
    """Permission and validation failures do not enter the retry loop."""
    sleeps: list[float] = []
    client, sdk = _client([failure], sleeps=sleeps)
    with pytest.raises(LLMError):
        client.complete([LLMMessage(role="user", content="hello")])
    assert len(sdk.responses.calls) == 1
    assert sleeps == []


@pytest.mark.parametrize(
    "failure",
    [APITimeoutError(), APIConnectionError(), InternalServerError()],
    ids=["timeout", "connection", "server"],
)
def test_openai_transport_and_server_failures_are_bounded(failure: Exception) -> None:
    """Timeout, connection, and server failures retry at most three times."""
    sleeps: list[float] = []
    client, sdk = _client([failure, failure, failure], sleeps=sleeps)
    with pytest.raises(LLMError):
        client.complete([LLMMessage(role="user", content="hello")])
    assert len(sdk.responses.calls) == 3
    assert sleeps == [1.0, 2.0]


@pytest.mark.parametrize(
    ("max_tokens", "temperature"),
    [(0, 0.2), ("512", 0.2), (512, -0.1), (512, 1.1), (512, "0.2")],
)
def test_openai_invalid_generation_options_fail_before_request(
    max_tokens: object, temperature: object
) -> None:
    """Invalid generation controls are rejected without a provider call."""
    client, sdk = _client([_response()])
    with pytest.raises(LLMError):
        client.complete(
            [LLMMessage(role="user", content="hello")],
            max_tokens=max_tokens,  # type: ignore[arg-type]
            temperature=temperature,  # type: ignore[arg-type]
        )
    assert sdk.responses.calls == []


def test_openai_logs_metadata_only(caplog: pytest.LogCaptureFixture) -> None:
    """Failure logs contain metadata but never credentials, prompts, or content."""
    secret = "sk-secret-for-log-test"
    prompt = "private prompt for log test"
    content = "private response content"
    client = OpenAIClient(
        model="gpt-test",
        api_key=secret,
        sdk_client=_SDKClient([AuthenticationError()]),
    )
    with caplog.at_level(logging.INFO, logger="yggdrasil.llm.openai"), pytest.raises(LLMError):
        client.complete([LLMMessage(role="user", content=prompt)])
    assert secret not in caplog.text
    assert prompt not in caplog.text
    assert content not in caplog.text


def test_openai_logs_only_endpoint_origin(caplog: pytest.LogCaptureFixture) -> None:
    """Custom endpoint path details are not included in adapter logs."""
    path_secret = "private-route-segment"
    with caplog.at_level(logging.INFO, logger="yggdrasil.llm.openai"):
        OpenAIClient(
            model="gemma-local",
            api_key="local-test",
            base_url=f"https://gateway.example/v1/{path_secret}",
            sdk_client=_SDKClient([_response()]),
        )
    assert "https://gateway.example" in caplog.text
    assert path_secret not in caplog.text


def test_openai_does_not_expose_streaming_or_implicit_endpoint_controls() -> None:
    """The adapter exposes a validated base URL but no streaming API."""
    assert not hasattr(OpenAIClient, "stream")
    assert "base_url" in OpenAIClient.__init__.__annotations__


def test_openai_retries_transient_failure_then_succeeds() -> None:
    """Transient failures use bounded backoff and can recover."""
    sleeps: list[float] = []
    client, sdk = _client([RateLimitError(), _response()], sleeps=sleeps)
    result = client.complete([LLMMessage(role="user", content="hello")])
    assert result.content == "ok"
    assert len(sdk.responses.calls) == 2
    assert sleeps == [1.0]


def test_openai_does_not_retry_permanent_failure() -> None:
    """Authentication failures propagate after one attempt."""
    sleeps: list[float] = []
    client, sdk = _client([AuthenticationError()], sleeps=sleeps)
    with pytest.raises(LLMError, match="AuthenticationError"):
        client.complete([LLMMessage(role="user", content="hello")])
    assert len(sdk.responses.calls) == 1
    assert sleeps == []


def test_openai_retry_exhaustion_is_explicit() -> None:
    """Three transient failures do not become a false success."""
    sleeps: list[float] = []
    client, sdk = _client([RateLimitError(), RateLimitError(), RateLimitError()], sleeps=sleeps)
    with pytest.raises(LLMError, match="RateLimitError"):
        client.complete([LLMMessage(role="user", content="hello")])
    assert len(sdk.responses.calls) == 3
    assert sleeps == [1.0, 2.0]


def test_existing_scripted_client_rejects_openai_only_options() -> None:
    """Existing providers do not silently drop new provider-specific options."""
    llm = ScriptedLLM(["ok"])
    with pytest.raises(LLMError, match="does not support"):
        llm.complete(
            [LLMMessage(role="user", content="hello")],
            options=LLMRequestOptions(reasoning_effort="low"),
        )


def test_existing_scripted_client_accepts_empty_options() -> None:
    """An explicitly empty options object remains equivalent to omitting options."""
    result = ScriptedLLM(["ok"]).complete(
        [LLMMessage(role="user", content="hello")],
        options=LLMRequestOptions(),
    )
    assert result.content == "ok"
