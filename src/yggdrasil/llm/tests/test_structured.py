"""Unit tests for LLM structured output extraction (thinking models)."""

from __future__ import annotations

from yggdrasil.llm.structured import (
    extract_json_array,
    extract_json_object,
    normalize_llm_text,
    strip_thinking_blocks,
)

_THINK_OPEN = "<" + "think" + ">"
_THINK_CLOSE = "</" + "think" + ">"
_THINKING_OPEN = "<thinking>"
_THINKING_CLOSE = "</thinking>"


def test_extract_json_array_clean() -> None:
    """Plain JSON array parses."""
    raw = '[{"name": "Payment API", "stereotype": "container", "confidence": 0.9}]'
    parsed = extract_json_array(raw)
    assert parsed is not None
    assert parsed[0]["name"] == "Payment API"


def test_extract_json_array_after_redacted_thinking_block() -> None:
    """JSON array after redacted thinking block."""
    raw = (
        _THINK_OPEN
        + "Scan README for containers."
        + _THINK_CLOSE
        + '\n[{"name": "Order Service", "stereotype": "container", "confidence": 0.93}]'
    )
    parsed = extract_json_array(raw)
    assert parsed is not None
    assert parsed[0]["name"] == "Order Service"


def test_extract_json_array_markdown_fence() -> None:
    """JSON array wrapped in markdown fence."""
    raw = '```json\n[{"name": "Billing Worker", "stereotype": "component"}]\n```'
    parsed = extract_json_array(raw)
    assert parsed is not None
    assert parsed[0]["name"] == "Billing Worker"


def test_extract_json_object_after_thinking_block() -> None:
    """Project map JSON object after thinking block."""
    raw = (
        _THINKING_OPEN
        + "Pick README and src paths."
        + _THINKING_CLOSE
        + '\n{"project_kind": "python-web", "targets": ["README.md"]}'
    )
    parsed = extract_json_object(raw)
    assert parsed is not None
    assert parsed["project_kind"] == "python-web"
    assert parsed["targets"] == ["README.md"]


def test_extract_json_array_rejects_prose_only() -> None:
    """Thinking-only prose without JSON returns None."""
    raw = _THINK_OPEN + "No architecture found." + _THINK_CLOSE
    assert extract_json_array(raw) is None


def test_strip_thinking_blocks_removes_redacted_reasoning() -> None:
    """Thinking wrapper is removed from normalized text."""
    raw = _THINK_OPEN + "reasoning here" + _THINK_CLOSE + "\n[]"
    assert strip_thinking_blocks(raw) == "[]"


def test_normalize_llm_text_composes_strips() -> None:
    """Normalization removes fences and thinking."""
    raw = _THINK_OPEN + "x" + _THINK_CLOSE + "\n```json\n[]\n```"
    assert normalize_llm_text(raw) == "[]"
