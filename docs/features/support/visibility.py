"""SSR visibility helpers for AT assertion steps (Django test client HTML)."""

from __future__ import annotations

import re

_GRAPH_ONLY_PANEL_TESTIDS = frozenset(
    {
        "browser-nav-panel",
        "browser-inspector-panel",
        "browser-toggle-nav-panel",
        "browser-toggle-inspector-panel",
    }
)

_CANVAS_CONTROL_TESTIDS = frozenset(
    {
        "browser-canvas-controls",
        "graph-replot-btn",
        "graph-zoom-in",
        "graph-zoom-out",
        "graph-zoom-fit",
        "graph-node-count",
    }
)


def browser_ssr_mode(content: str) -> str | None:
    """Return ``table`` or ``graph`` from ``#browserRoot`` SSR class, if present."""
    for match in re.finditer(r"<div[^>]+>", content):
        tag = match.group(0)
        if "browserRoot" not in tag and "yrg-browser-root" not in tag:
            continue
        mode_match = re.search(r"\byrg-mode-(table|graph)\b", tag)
        if mode_match:
            return mode_match.group(1)
    return None


def opening_tag_for_testid(content: str, test_id: str) -> str | None:
    """Return the opening HTML tag that carries ``data-testid=test_id``, if any."""
    pattern = rf'<([a-zA-Z][\w-]*)[^>]*\bdata-testid="{re.escape(test_id)}"[^>]*>'
    match = re.search(pattern, content)
    return match.group(0) if match else None


def is_element_ssr_hidden(content: str, test_id: str) -> bool:
    """
    Decide whether an element is hidden by server-rendered markup.

    Covers ``d-none`` on the element, ``yrg-graph-only`` panels in table mode,
    and graph canvas controls that only render for ``mode=graph``.
    """
    tag = opening_tag_for_testid(content, test_id)
    if tag is None:
        return True
    if re.search(r"\bd-none\b", tag):
        return True
    mode = browser_ssr_mode(content)
    if mode != "table":
        return False
    if "yrg-graph-only" in tag:
        return True
    if test_id in _CANVAS_CONTROL_TESTIDS:
        return True
    if test_id == "graph-cy-container":
        return bool(re.search(r'id="graphView"[^>]*\bd-none\b', content))
    return False


def assert_testid_visible(content: str, test_id: str) -> None:
    """Raise ``AssertionError`` when ``test_id`` is absent or SSR-hidden."""
    tag = opening_tag_for_testid(content, test_id)
    if tag is None:
        msg = f"Element {test_id!r} not found (no data-testid={test_id!r} in response)"
        raise AssertionError(msg)
    if is_element_ssr_hidden(content, test_id):
        msg = f"Element {test_id!r} is present in HTML but SSR-hidden"
        raise AssertionError(msg)


def assert_testid_hidden(content: str, test_id: str) -> None:
    """Raise ``AssertionError`` when ``test_id`` is visible in SSR markup."""
    if not is_element_ssr_hidden(content, test_id):
        msg = f"Expected element {test_id!r} to be SSR-hidden, but it appears visible"
        raise AssertionError(msg)


def graph_only_panel_testids() -> frozenset[str]:
    """Testids for left/right explorer panels hidden in table mode."""
    return _GRAPH_ONLY_PANEL_TESTIDS
