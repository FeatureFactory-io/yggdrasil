"""Tests for ratatosk.discovery.prefilter."""

from __future__ import annotations

from ratatosk.discovery.prefilter import prefilter_candidates


def test_prefilter_rejects_feature_file_only_candidates() -> None:
    """Payment API from Gherkin feature file alone is rejected."""
    candidates = [
        {
            "name": "Payment API",
            "stereotype": "container",
            "confidence": 0.95,
            "source_paths": ["docs/features/act-1-ratatosk/ratatosk-discovery.feature"],
        }
    ]
    result = prefilter_candidates(candidates)
    assert result.kept == []
    assert result.rejected[0]["name"] == "Payment API"


def test_prefilter_keeps_sao_auth_component() -> None:
    """auth from SAO.md is kept."""
    candidates = [
        {
            "name": "auth",
            "stereotype": "component",
            "confidence": 0.9,
            "source_paths": ["docs/architecture/SAO.md"],
        }
    ]
    result = prefilter_candidates(candidates)
    assert len(result.kept) == 1
    assert result.kept[0]["name"] == "auth"


def test_prefilter_keeps_mixed_source_candidate() -> None:
    """Candidate with SAO + feature sources is kept (not noise-only)."""
    candidates = [
        {
            "name": "Order Service",
            "stereotype": "container",
            "confidence": 0.9,
            "source_paths": [
                "docs/architecture/SAO.md",
                "docs/features/act-1-ratatosk/ratatosk-discovery.feature",
            ],
        }
    ]
    result = prefilter_candidates(candidates)
    assert len(result.kept) == 1
