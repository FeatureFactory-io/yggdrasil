"""
Structured output extraction from LLM responses.

Thinking models (Qwen3, Claude extended thinking, OpenAI reasoning) often wrap
JSON in reasoning traces or markdown fences. Adapters should isolate thinking
into ``LLMResponse.thinking``; this module normalizes ``content`` for parsing.

Used by Ratatosk discovery (runner + agent) for map/extract JSON steps.
"""

from __future__ import annotations

import json
import logging
import re

logger = logging.getLogger("yggdrasil.llm.structured")

_THINKING_BLOCK_RE = re.compile(
    r"<\s*think(?:ing)?\s*>[\s\S]*?<\s*/\s*think(?:ing)?\s*>",
    re.IGNORECASE,
)
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)


def strip_thinking_blocks(text: str) -> str:
    """
    Remove inline thinking/reasoning blocks from model output.

    Handles `` and `` tags (Qwen3 and similar).

    :param text: Raw model text that may contain thinking wrappers.
    :return: Text with thinking blocks removed.
    """
    if not text:
        return ""
    cleaned = _THINKING_BLOCK_RE.sub("", text)
    return cleaned.strip()


def strip_markdown_fence(text: str) -> str:
    """
    Remove a single surrounding markdown code fence if present.

    :param text: Candidate JSON text, optionally fenced.
    :return: Inner content when fenced; otherwise unchanged trimmed text.
    """
    stripped = (text or "").strip()
    match = _FENCE_RE.match(stripped)
    if match:
        return match.group(1).strip()
    if stripped.startswith("```"):
        inner = stripped.strip("`")
        if inner.lower().startswith("json"):
            inner = inner[4:].lstrip()
        return inner.strip()
    return stripped


def normalize_llm_text(raw: str) -> str:
    """
    Prepare LLM answer text for structured JSON extraction.

    Strips thinking blocks and markdown fences; does not parse JSON.

    :param raw: ``LLMResponse.content`` after adapter-level thinking isolation.
    :return: Normalized text safe to pass to ``extract_json_*``.
    """
    text = strip_thinking_blocks(raw or "")
    return strip_markdown_fence(text)


def extract_json_array(raw: str) -> list[dict] | None:
    """
    Parse a JSON array of dicts from LLM output.

    :param raw: Model content (may include thinking or fences).
    :return: List of dicts when valid array found; otherwise ``None``.
    """
    text = normalize_llm_text(raw)
    if not text:
        logger.info("extract_json_array | result=empty_input")
        return None
    data = _load_json_or_slice(text, start_char="[", end_char="]")
    if not isinstance(data, list):
        logger.info("extract_json_array | result=not_array type=%s", type(data).__name__)
        return None
    items = [item for item in data if isinstance(item, dict) and item.get("name")]
    logger.info(
        "extract_json_array | result=ok items=%s raw_len=%s",
        len(items),
        len(raw or ""),
    )
    return items


def extract_json_object(raw: str) -> dict | None:
    """
    Parse a JSON object from LLM output.

    :param raw: Model content (may include thinking or fences).
    :return: Dict when valid object found; otherwise ``None``.
    """
    text = normalize_llm_text(raw)
    if not text:
        logger.info("extract_json_object | result=empty_input")
        return None
    data = _load_json_or_slice(text, start_char="{", end_char="}")
    if not isinstance(data, dict):
        logger.info("extract_json_object | result=not_object type=%s", type(data).__name__)
        return None
    logger.info("extract_json_object | result=ok keys=%s raw_len=%s", len(data), len(raw or ""))
    return data


def _load_json_or_slice(text: str, *, start_char: str, end_char: str) -> object | None:
    """Try full-text JSON parse, then bracket/brace slice fallback."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start < 0 or end <= start:
            logger.info(
                "_load_json_or_slice | result=parse_fail start=%s end=%s",
                start_char,
                end_char,
            )
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            logger.info("_load_json_or_slice | result=slice_parse_fail")
            return None
