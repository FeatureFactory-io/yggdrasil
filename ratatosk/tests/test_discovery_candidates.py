"""Tests for ratatosk.discovery.candidates provenance helpers."""

from __future__ import annotations

from ratatosk.discovery.candidates import attach_source_paths, merge_candidates_by_slug


def test_attach_source_paths_tags_each_candidate() -> None:
    raw = [{"name": "Payment API", "stereotype": "container", "confidence": 0.9}]
    tagged = attach_source_paths(raw, "src/payment_api/app.py")
    assert tagged[0]["source_paths"] == ["src/payment_api/app.py"]


def test_merge_candidates_unions_source_paths() -> None:
    a = {
        "name": "Backend",
        "stereotype": "container",
        "confidence": 0.8,
        "source_paths": ["README.md"],
    }
    b = {
        "name": "Backend container",
        "stereotype": "container",
        "confidence": 0.95,
        "source_paths": ["docs/architecture/SAO.md"],
    }
    merged = merge_candidates_by_slug([a, b])
    assert len(merged) == 2


def test_merge_candidates_keeps_higher_confidence_same_slug() -> None:
    low = {
        "name": "Redis",
        "stereotype": "container",
        "confidence": 0.7,
        "source_paths": ["docker-compose.yml"],
    }
    high = {
        "name": "Redis",
        "stereotype": "container",
        "confidence": 0.95,
        "source_paths": ["docs/architecture/SAO.md"],
    }
    merged = merge_candidates_by_slug([low, high])
    assert len(merged) == 1
    assert merged[0]["confidence"] == 0.95
    assert set(merged[0]["source_paths"]) == {
        "docker-compose.yml",
        "docs/architecture/SAO.md",
    }
