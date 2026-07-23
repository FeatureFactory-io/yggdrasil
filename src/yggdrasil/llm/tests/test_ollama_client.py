"""Unit tests for OllamaClient (ACT-1-LLM-01)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from yggdrasil.llm.adapters.ollama import OllamaClient
from yggdrasil.llm.base import LLMError, LLMMessage


def test_ollama_client_build_payload() -> None:
    """Payload includes model, messages, and options."""
    client = OllamaClient(model="qwen3:14b", base_url="http://localhost:11434")
    payload = client._build_payload(
        [LLMMessage(role="user", content="hello")],
        system="sys",
        max_tokens=512,
        temperature=0.1,
    )
    assert payload["model"] == "qwen3:14b"
    assert payload["stream"] is False
    assert payload["messages"][0]["role"] == "system"
    assert payload["options"]["num_predict"] == 512


def test_ollama_client_parse_response() -> None:
    """Parse Ollama JSON into LLMResponse."""
    client = OllamaClient()
    resp = client._parse_response(
        {
            "model": "qwen3:14b",
            "message": {"role": "assistant", "content": "[]"},
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 5,
        }
    )
    assert resp.content == "[]"
    assert resp.model == "qwen3:14b"
    assert resp.usage["input"] == 10
    assert resp.thinking == ""


def test_ollama_client_parse_response_thinking_field() -> None:
    """Ollama thinking field is isolated from answer content."""
    client = OllamaClient()
    resp = client._parse_response(
        {
            "model": "qwen3:14b",
            "message": {
                "role": "assistant",
                "thinking": "Scanning README for containers.",
                "content": '[{"name": "Payment API", "stereotype": "container"}]',
            },
            "done": True,
        }
    )
    assert resp.thinking == "Scanning README for containers."
    assert resp.content.startswith("[{")


def test_ollama_client_parse_response_inline_thinking() -> None:
    """Inline think tags are stripped from content."""
    think_open = "<" + "think" + ">"
    think_close = "</" + "think" + ">"
    client = OllamaClient()
    resp = client._parse_response(
        {
            "model": "qwen3:14b",
            "message": {
                "role": "assistant",
                "content": (
                    think_open
                    + "Analyze paths."
                    + think_close
                    + '\n{"project_kind": "web", "targets": ["README.md"]}'
                ),
            },
            "done": True,
        }
    )
    assert resp.content.startswith('{"project_kind"')


def test_ollama_default_timeout_is_300_seconds() -> None:
    """Thinking models may exceed 120s per call during bootstrap."""
    from yggdrasil.llm.adapters import ollama as ollama_mod

    assert ollama_mod._DEFAULT_TIMEOUT == 300.0


def test_ollama_default_max_tokens_is_8000() -> None:
    """Field-tier default max_tokens supports thinking model headroom."""
    import inspect

    sig = inspect.signature(OllamaClient.complete)
    assert sig.parameters["max_tokens"].default == 8000


@patch("httpx.Client")
def test_ollama_complete_success(mock_client_cls) -> None:
    """complete() posts to /api/chat and returns content."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "model": "qwen3:14b",
        "message": {"content": '{"targets": []}'},
        "done": True,
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.return_value = mock_response
    mock_client_cls.return_value = mock_client

    client = OllamaClient(model="qwen3:14b", base_url="http://localhost:11434")
    resp = client.complete([LLMMessage(role="user", content="map tree")])
    assert '{"targets"' in resp.content
    mock_client.post.assert_called_once()


@patch("httpx.Client")
def test_ollama_complete_connection_error(mock_client_cls) -> None:
    """Connection failure raises LLMError."""
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.post.side_effect = httpx.ConnectError("refused")
    mock_client_cls.return_value = mock_client

    client = OllamaClient()
    with pytest.raises(LLMError, match="Ollama request failed"):
        client.complete([LLMMessage(role="user", content="x")])


def test_llm02_model_not_in_env_uses_default() -> None:
    """LLM-02: missing LLM_OLLAMA_MODEL uses qwen3:14b default."""
    client = OllamaClient(base_url="http://localhost:11434")
    assert client.model_id == "qwen3:14b"
