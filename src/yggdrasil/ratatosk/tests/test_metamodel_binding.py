"""Pytest for Ratatosk Metamodel slug resolution and Model binding."""

from __future__ import annotations

import pytest
from tests.fixtures.factories.model_factories import MetamodelFactory, YggdrasilModelFactory

from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.ratatosk.agent import _ensure_model, _metamodel_guidance, _resolve_metamodel


@pytest.mark.django_db
def test_resolve_metamodel_c4_ensures_catalog() -> None:
    """Resolving c4 creates the canonical catalog."""
    mm = _resolve_metamodel("c4")
    assert mm.slug == "c4"
    assert mm.stereotypes.filter(slug="container").exists()


@pytest.mark.django_db
def test_ensure_model_rejects_metamodel_mismatch() -> None:
    """Existing Model cannot be rebound to a different Metamodel slug."""
    c4 = ensure_c4_metamodel()
    other = MetamodelFactory(name="Other", slug="other")
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=c4)
    with pytest.raises(ValueError, match="bound to metamodel"):
        _ensure_model("Yggdrasil", other.slug)


@pytest.mark.django_db
def test_metamodel_guidance_lists_ontology() -> None:
    """Guidance payload includes stereotype and package slugs."""
    mm = ensure_c4_metamodel()
    text = _metamodel_guidance(mm)
    assert "element_stereotypes=" in text
    assert "container" in text
    assert "packages=" in text
    assert "technology" in text
