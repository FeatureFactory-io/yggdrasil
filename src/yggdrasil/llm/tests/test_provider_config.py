"""Unit tests for provider-neutral model and endpoint configuration."""

from __future__ import annotations

import pytest

from yggdrasil.llm.provider_config import (
    DEFAULT_OPENAI_MODEL,
    resolve_model_id,
    resolve_openai_base_url,
)


def test_openai_model_resolution_accepts_opaque_compatible_model_id() -> None:
    """Explicit compatible-server model IDs are never restricted by prefix."""
    model_id = "gemma-4-e4b-uncensored-hauhaucs-aggressive"
    assert resolve_model_id("openai", model_id, default_model=DEFAULT_OPENAI_MODEL) == model_id


def test_openai_model_resolution_rejects_known_foreign_alias() -> None:
    """A Claude symbolic alias cannot silently cross the OpenAI boundary."""
    with pytest.raises(ValueError, match="provider openai"):
        resolve_model_id("openai", "sonnet5", default_model=DEFAULT_OPENAI_MODEL)


def test_openai_base_url_accepts_loopback_responses_endpoint() -> None:
    """LM Studio's explicit loopback Responses API base URL is preserved."""
    assert (
        resolve_openai_base_url("http://127.0.0.1:1234/v1/")
        == "http://127.0.0.1:1234/v1"
    )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://example.test/v1",
        "ftp://127.0.0.1:1234/v1",
        "http://token@127.0.0.1:1234/v1",
        "http://127.0.0.1:1234/v1?token=secret",
        "not a url",
    ],
)
def test_openai_base_url_rejects_unsafe_or_malformed_value(base_url: str) -> None:
    """Unsafe endpoint values fail before an SDK client can be constructed."""
    with pytest.raises(ValueError, match="OPENAI_BASE_URL"):
        resolve_openai_base_url(base_url)
