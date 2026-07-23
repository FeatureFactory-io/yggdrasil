"""Pytest for Ratatosk Metamodel slug resolution and real LLM guidance."""

from __future__ import annotations

import pytest
from tests.fixtures.factories.model_factories import MetamodelFactory, YggdrasilModelFactory

from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.ratatosk.agent import (
    _constrain_candidates_to_metamodel,
    _ensure_model,
    _metamodel_guidance,
    _parse_candidate_json,
    _resolve_metamodel,
)


@pytest.mark.django_db
def test_resolve_metamodel_c4_ensures_catalog() -> None:
    """Resolving c4 creates the canonical catalog with guidance fields."""
    mm = _resolve_metamodel("c4")
    assert mm.slug == "c4"
    container = mm.stereotypes.get(slug="container")
    assert container.description
    assert container.property_schema.get("properties")
    assert "calls" in container.allowed_edge_rules


@pytest.mark.django_db
def test_ensure_model_rejects_metamodel_mismatch() -> None:
    """Existing Model cannot be rebound to a different Metamodel slug."""
    c4 = ensure_c4_metamodel()
    other = MetamodelFactory(name="Other", slug="other")
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=c4)
    with pytest.raises(ValueError, match="bound to metamodel"):
        _ensure_model("Yggdrasil", other.slug)


@pytest.mark.django_db
def test_metamodel_guidance_is_detailed_instruction_text() -> None:
    """Guidance must include descriptions, schemas, and rules — not a slug list."""
    mm = ensure_c4_metamodel()
    text = _metamodel_guidance(mm)
    assert "# Metamodel: C4" in text
    assert "### `container`" in text
    assert "When to use:" in text
    assert "property_schema:" in text
    assert "technology" in text
    assert "allowed_edge_rules" in text
    assert "Do not invent slugs" in text


@pytest.mark.django_db
def test_constrain_candidates_drops_unknown_stereotype() -> None:
    """Candidates inventing types are rejected against the Metamodel catalog."""
    mm = ensure_c4_metamodel()
    accepted = _constrain_candidates_to_metamodel(
        [
            {
                "name": "Payment API",
                "stereotype": "Container",
                "package": "Technology",
                "confidence": 0.9,
            },
            {
                "name": "Invented Thing",
                "stereotype": "Microservice",
                "package": "Technology",
                "confidence": 0.9,
            },
        ],
        mm,
    )
    assert len(accepted) == 1
    assert accepted[0]["name"] == "Payment API"
    assert accepted[0]["stereotype"] == "container"
    assert accepted[0]["package"] == "technology"


def test_parse_candidate_json_accepts_array() -> None:
    """LLM JSON array of candidates is parsed."""
    raw = (
        '[{"name": "Payment API", "stereotype": "container", '
        '"package": "technology", "confidence": 0.9}]'
    )
    parsed = _parse_candidate_json(raw)
    assert parsed is not None
    assert parsed[0]["name"] == "Payment API"


def test_parse_candidate_json_rejects_prose() -> None:
    """Non-JSON prose returns None (no silent hardcoded candidate fallback)."""
    assert _parse_candidate_json("NER scan complete for bootstrap") is None
