"""Assertion step unit tests for View Browser layout."""

from __future__ import annotations

import sys
from pathlib import Path

_FEATURES_ROOT = Path(__file__).resolve().parents[2] / "docs" / "features"
if str(_FEATURES_ROOT) not in sys.path:
    sys.path.insert(0, str(_FEATURES_ROOT))

from steps import assertion_steps  # noqa: E402


class _FakeContext:
    response = None


def test_layout_class_assertion_passes() -> None:
    """Layout step detects yrg-view-browser on body."""
    ctx = _FakeContext()
    ctx.response = type(
        "R",
        (),
        {"content": b'<html><body class="yrg-view-browser"><main></main></body></html>'},
    )()
    assertion_steps.step_page_uses_view_browser_layout(ctx)


def test_embed_partial_assertion_passes() -> None:
    """Embed partial step rejects full chrome markers."""
    ctx = _FakeContext()
    ctx.response = type("R", (), {"content": b'<div data-testid="inspector-empty">ok</div>'})()
    assertion_steps.step_response_is_embed_partial(ctx)
