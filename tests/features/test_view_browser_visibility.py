"""SSR visibility helper unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_FEATURES_ROOT = Path(__file__).resolve().parents[2] / "docs" / "features"
if str(_FEATURES_ROOT) not in sys.path:
    sys.path.insert(0, str(_FEATURES_ROOT))

from support.visibility import (  # noqa: E402
    assert_testid_hidden,
    assert_testid_visible,
    is_element_ssr_hidden,
)

_TABLE_MODE_SNIPPET = """
<style>.yrg-mode-table .yrg-graph-only { display: none; }</style>
<div id="browserRoot" class="yrg-browser-root yrg-mode-table flex-grow-1">
  <aside class="yrg-browser-nav yrg-graph-only" data-testid="browser-nav-panel"></aside>
  <div id="graphView" class="yrg-browser-canvas d-none">
    <div id="cy" data-testid="graph-cy-container"></div>
  </div>
  <div class="yrg-canvas-controls d-none" data-testid="browser-canvas-controls">
    <button data-testid="graph-replot-btn">↺</button>
  </div>
</div>
"""

_GRAPH_MODE_SNIPPET = """
<style>.yrg-mode-table .yrg-graph-only { display: none; }</style>
<div id="browserRoot" class="yrg-browser-root yrg-mode-graph flex-grow-1">
  <aside class="yrg-browser-nav yrg-graph-only" data-testid="browser-nav-panel"></aside>
  <div id="graphView" class="yrg-browser-canvas">
    <div id="cy" data-testid="graph-cy-container"></div>
  </div>
  <div class="yrg-canvas-controls" data-testid="browser-canvas-controls">
    <button data-testid="graph-replot-btn">↺</button>
  </div>
</div>
"""


def test_table_mode_hides_graph_only_panels() -> None:
    """Graph-only panels and canvas controls are SSR-hidden in table mode."""
    assert is_element_ssr_hidden(_TABLE_MODE_SNIPPET, "browser-nav-panel")
    assert is_element_ssr_hidden(_TABLE_MODE_SNIPPET, "graph-cy-container")
    assert is_element_ssr_hidden(_TABLE_MODE_SNIPPET, "graph-replot-btn")


def test_graph_mode_shows_canvas_controls() -> None:
    """Canvas controls and cytoscape container are visible in graph mode."""
    assert not is_element_ssr_hidden(_GRAPH_MODE_SNIPPET, "browser-nav-panel")
    assert not is_element_ssr_hidden(_GRAPH_MODE_SNIPPET, "graph-cy-container")
    assert not is_element_ssr_hidden(_GRAPH_MODE_SNIPPET, "graph-replot-btn")


def test_assert_testid_visible_raises_when_hidden() -> None:
    """assert_testid_visible rejects SSR-hidden markers."""
    with pytest.raises(AssertionError, match="SSR-hidden"):
        assert_testid_visible(_TABLE_MODE_SNIPPET, "graph-replot-btn")


def test_assert_testid_hidden_passes_for_table_mode_controls() -> None:
    """assert_testid_hidden accepts hidden canvas controls."""
    assert_testid_hidden(_TABLE_MODE_SNIPPET, "graph-replot-btn")
