"""
FactoryBoy factories for core graph entities.

Covers Metamodel + all graph models:
  MetamodelFactory, YggdrasilModelFactory, StereotypeFactory, PackageFactory,
  DiagramFactory, ElementFactory, RelationshipFactory.
"""

from __future__ import annotations

import factory
from django.utils.text import slugify

from yggdrasil.graph.models import (
    Diagram,
    Element,
    Metamodel,
    Package,
    Relationship,
    Stereotype,
    YggdrasilModel,
    ensure_c4_metamodel,
)


class MetamodelFactory(factory.django.DjangoModelFactory):
    """
    Build a :class:`~yggdrasil.graph.models.Metamodel`.

    Defaults to the canonical C4 profile (get_or_create by slug).

    :Example:

    >>> mm = MetamodelFactory()
    >>> mm.slug
    'c4'
    """

    class Meta:
        model = Metamodel
        django_get_or_create = ("slug",)

    name = "C4"
    slug = Metamodel.SLUG_C4
    description = "C4 architecture metamodel"


class YggdrasilModelFactory(factory.django.DjangoModelFactory):
    """
    Build a :class:`~yggdrasil.graph.models.YggdrasilModel`.

    :Example:

    >>> m = YggdrasilModelFactory()
    >>> m.slug  # auto-generated from name
    'model-0'
    """

    class Meta:
        model = YggdrasilModel
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Model {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    metamodel = factory.SubFactory(MetamodelFactory)


class StereotypeFactory(factory.django.DjangoModelFactory):
    """
    Build a :class:`~yggdrasil.graph.models.Stereotype` on a Metamodel.

    :Example:

    >>> st = StereotypeFactory(is_edge=False)
    >>> st.slug
    'stereotype-0'
    """

    class Meta:
        model = Stereotype
        django_get_or_create = ("metamodel", "slug")

    metamodel = factory.SubFactory(MetamodelFactory)
    name = factory.Sequence(lambda n: f"Stereotype {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    is_edge = False
    property_schema = factory.LazyFunction(dict)
    allowed_edge_rules = factory.LazyFunction(list)


class EdgeStereotypeFactory(StereotypeFactory):
    """
    Build an edge :class:`~yggdrasil.graph.models.Stereotype` (``is_edge=True``).

    :Example:

    >>> st = EdgeStereotypeFactory()
    >>> st.is_edge
    True
    """

    name = factory.Sequence(lambda n: f"Edge {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    is_edge = True


class PackageFactory(factory.django.DjangoModelFactory):
    """
    Build a :class:`~yggdrasil.graph.models.Package` on a Metamodel.

    :Example:

    >>> pkg = PackageFactory()
    >>> pkg.slug
    'package-0'
    """

    class Meta:
        model = Package
        django_get_or_create = ("metamodel", "slug")

    metamodel = factory.SubFactory(MetamodelFactory)
    name = factory.Sequence(lambda n: f"Package {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    parent = None


class DiagramFactory(factory.django.DjangoModelFactory):
    """
    Build a :class:`~yggdrasil.graph.models.Diagram`.

    :Example:

    >>> d = DiagramFactory()
    >>> d.diagram_type
    'context'
    """

    class Meta:
        model = Diagram

    model = factory.SubFactory(YggdrasilModelFactory)
    package = factory.SubFactory(
        PackageFactory,
        metamodel=factory.SelfAttribute("..model.metamodel"),
    )
    name = factory.Sequence(lambda n: f"Diagram {n}")
    diagram_type = Diagram.TYPE_CONTEXT
    layout_data = factory.LazyFunction(dict)


class ElementFactory(factory.django.DjangoModelFactory):
    """
    Build a graph :class:`~yggdrasil.graph.models.Element` (a node).

    :Example:

    >>> e = ElementFactory()
    >>> e.source
    'human'
    """

    class Meta:
        model = Element
        django_get_or_create = ("model", "slug")

    model = factory.SubFactory(YggdrasilModelFactory)
    name = factory.Sequence(lambda n: f"Element {n}")
    slug = factory.LazyAttribute(lambda o: slugify(o.name))
    stereotype = factory.SubFactory(
        StereotypeFactory,
        metamodel=factory.SelfAttribute("..model.metamodel"),
    )
    package = factory.SubFactory(
        PackageFactory,
        metamodel=factory.SelfAttribute("..model.metamodel"),
    )
    properties = factory.LazyFunction(dict)
    source = Element.SOURCE_HUMAN
    confidence = 1.0


class RelationshipFactory(factory.django.DjangoModelFactory):
    """
    Build a graph :class:`~yggdrasil.graph.models.Relationship` (a directed edge).

    :Example:

    >>> r = RelationshipFactory()
    >>> r.confidence
    1.0
    """

    class Meta:
        model = Relationship

    model = factory.SubFactory(YggdrasilModelFactory)
    source = factory.SubFactory(ElementFactory, model=factory.SelfAttribute("..model"))
    target = factory.SubFactory(ElementFactory, model=factory.SelfAttribute("..model"))
    stereotype = factory.SubFactory(
        EdgeStereotypeFactory,
        metamodel=factory.SelfAttribute("..model.metamodel"),
    )
    properties = factory.LazyFunction(dict)
    confidence = 1.0


def ensure_seeded_c4_metamodel() -> Metamodel:
    """Factory helper: ensure canonical C4 catalog exists (stereotypes + packages)."""
    return ensure_c4_metamodel()
