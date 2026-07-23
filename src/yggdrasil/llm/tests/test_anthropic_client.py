"""Unit tests for AnthropicClient (ACT-1-LLM-ANTHROPIC slices 2-4)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from yggdrasil.llm.adapters.anthropic import AnthropicClient
from yggdrasil.llm.base import LLMError, LLMMessage


@pytest.fixture
def client() -> AnthropicClient:
    return AnthropicClient(model="claude-3-5-haiku-20241022", api_key="sk-test")


def test_anthropic_parse_response_text_only(client: AnthropicClient) -> None:
    """Text block populates content; thinking empty."""
    resp = client._parse_response(
        {
            "model": "claude-3-5-haiku-20241022",
            "content": [{"type": "text", "text": "[]"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 12, "output_tokens": 3},
        }
    )
    assert resp.content == "[]"
    assert resp.thinking == ""
    assert resp.model == "claude-3-5-haiku-20241022"
    assert resp.usage == {"input": 12, "output": 3}
    assert resp.stop_reason == "end_turn"


def test_anthropic_parse_response_isolates_thinking_blocks(client: AnthropicClient) -> None:
    """Thinking and text blocks map to separate LLMResponse fields."""
    resp = client._parse_response(
        {
            "model": "claude-3-5-haiku-20241022",
            "content": [
                {"type": "thinking", "thinking": "Scan README for containers."},
                {"type": "text", "text": '[{"name": "Payment API"}]'},
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 20, "output_tokens": 40},
        }
    )
    assert resp.thinking == "Scan README for containers."
    assert resp.content.startswith("[{")
    assert resp.usage["input"] == 20


def test_anthropic_init_missing_key_raises_llm_error() -> None:
    """Empty api_key raises LLMError before SDK call."""
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        AnthropicClient(model="claude-3-5-haiku-20241022", api_key="")


def test_anthropic_build_payload_includes_system_and_messages(client: AnthropicClient) -> None:
    """Payload separates system prompt and user messages with max_tokens=8000."""
    payload = client._build_payload(
        [LLMMessage(role="user", content="hello")],
        system="sys",
        max_tokens=8000,
        temperature=0.2,
    )
    assert payload["model"] == "claude-3-5-haiku-20241022"
    assert payload["system"] == "sys"
    assert payload["max_tokens"] == 8000
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert payload["temperature"] == 0.2


def test_anthropic_complete_posts_to_messages_api(client: AnthropicClient) -> None:
    """Mock SDK messages.create; returns parsed LLMResponse."""
    mock_message = MagicMock()
    mock_message.model_dump.return_value = {
        "model": "claude-3-5-haiku-20241022",
        "content": [{"type": "text", "text": "ok"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.return_value = mock_message
        resp = client.complete([LLMMessage(role="user", content="hi")], system="sys")
    assert resp.content == "ok"
    mock_cls.return_value.messages.create.assert_called_once()


def test_anthropic_complete_sdk_error_raises_llm_error(client: AnthropicClient) -> None:
    """SDK APIError maps to LLMError with model id, no key leak."""
    import anthropic

    with patch("anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = anthropic.APIError(
            message="rate limited",
            request=MagicMock(),
            body=None,
        )
        with pytest.raises(LLMError, match="claude-3-5-haiku"):
            client.complete([LLMMessage(role="user", content="hi")])
