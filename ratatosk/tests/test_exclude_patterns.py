"""Unit tests for Ratatosk exclude pattern matching."""

from __future__ import annotations

from pathlib import Path

from ratatosk.discovery.exclude import (
    merge_bootstrap_exclude_patterns,
    normalize_exclude_patterns,
    path_is_excluded,
)
from ratatosk.discovery.runner import _build_file_tree


def test_normalize_exclude_patterns_splits_csv() -> None:
    """Comma-separated exclude env values become a list."""
    assert normalize_exclude_patterns("src/payment_api/,docs/") == [
        "src/payment_api/",
        "docs/",
    ]


def test_path_is_excluded_prefix() -> None:
    """Directory prefix patterns skip nested paths."""
    patterns = ["src/payment_api/"]
    assert path_is_excluded("src/payment_api/app.py", patterns)
    assert not path_is_excluded("src/order_service/app.py", patterns)


def test_path_is_excluded_glob() -> None:
    """Simple globs skip matching filenames."""
    patterns = ["*.md"]
    assert path_is_excluded("docs/README.md", patterns)
    assert not path_is_excluded("src/app.py", patterns)


def test_merge_bootstrap_exclude_adds_cursor() -> None:
    """Bootstrap merge always adds .cursor/** alongside operator patterns."""
    merged = merge_bootstrap_exclude_patterns(["docs/plans/"])
    assert any("docs/plans" in p for p in merged)
    assert ".cursor/**" in merged


def test_build_file_tree_applies_exclude(tmp_path: Path) -> None:
    """Filesystem scan skips excluded paths and reports skip count."""
    (tmp_path / "README.md").write_text("# demo", encoding="utf-8")
    payment_dir = tmp_path / "src" / "payment_api"
    payment_dir.mkdir(parents=True)
    (payment_dir / "app.py").write_text("app", encoding="utf-8")
    order_dir = tmp_path / "src" / "order_service"
    order_dir.mkdir(parents=True)
    (order_dir / "app.py").write_text("app", encoding="utf-8")

    paths, skipped = _build_file_tree(str(tmp_path), ["src/payment_api/"])
    assert "src/payment_api/app.py" not in paths
    assert "src/order_service/app.py" in paths
    assert skipped >= 1
