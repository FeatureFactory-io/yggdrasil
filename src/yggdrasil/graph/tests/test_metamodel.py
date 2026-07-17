"""Pytest for first-class Metamodel ownership and Model immutability."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from tests.fixtures.factories.model_factories import (
    MetamodelFactory,
    StereotypeFactory,
    YggdrasilModelFactory,
)

from yggdrasil.graph.models import Metamodel, Stereotype, ensure_c4_metamodel


@pytest.mark.django_db
def test_ensure_c4_metamodel_seeds_stereotypes_and_packages() -> None:
    """C4 Metamodel owns canonical stereotypes and packages."""
    mm = ensure_c4_metamodel()
    assert mm.slug == Metamodel.SLUG_C4
    assert mm.stereotypes.filter(slug="container", is_edge=False).exists()
    assert mm.stereotypes.filter(slug="depends_on", is_edge=True).exists()
    assert mm.packages.filter(slug="technology").exists()


@pytest.mark.django_db
def test_model_metamodel_is_immutable_after_create() -> None:
    """Changing Model.metamodel after create raises ValidationError."""
    c4 = ensure_c4_metamodel()
    other = MetamodelFactory(name="Other", slug="other")
    model = YggdrasilModelFactory(name="Bound", slug="bound", metamodel=c4)
    model.metamodel = other
    with pytest.raises(ValidationError, match="cannot be changed"):
        model.save()


@pytest.mark.django_db
def test_stereotype_belongs_to_metamodel_not_model() -> None:
    """Stereotypes are scoped to Metamodel; multiple Models share the catalog."""
    mm = ensure_c4_metamodel()
    m1 = YggdrasilModelFactory(name="One", slug="one", metamodel=mm)
    m2 = YggdrasilModelFactory(name="Two", slug="two", metamodel=mm)
    st = StereotypeFactory(metamodel=mm, name="Container", slug="container")
    assert st.metamodel_id == mm.pk
    assert m1.metamodel_id == m2.metamodel_id == mm.pk
    field_names = {f.name for f in Stereotype._meta.fields}
    assert "metamodel" in field_names
    assert "model" not in field_names
