"""
FactoryBoy factories for core graph entities (``Element``, ``Relationship``).

Skeleton stubs (``do-skeletons-first.mdc``): the ``graph`` app
(``src/yggdrasil/graph/``) has no models yet — only ``apps.py``. These
factories document the intended shape from SAO.md §1/§4 and must be
implemented in lockstep with the ``graph`` models when that app is built.
"""

from __future__ import annotations

import factory


class ElementFactory(factory.django.DjangoModelFactory):
    """
    Build a graph ``Element`` (a node: class, service, module, etc.).

    :raises NotImplementedError: until ``yggdrasil.graph.models.Element``
        exists. Implement alongside the ``graph`` app's models.
    """

    class Meta:
        abstract = True

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError(
            "ElementFactory is a skeleton stub — implement once "
            "yggdrasil.graph.models.Element exists."
        )


class RelationshipFactory(factory.django.DjangoModelFactory):
    """
    Build a graph ``Relationship`` (an edge between two Elements).

    :raises NotImplementedError: until ``yggdrasil.graph.models.Relationship``
        exists. Implement alongside the ``graph`` app's models.
    """

    class Meta:
        abstract = True

    def __new__(cls, *args, **kwargs):
        raise NotImplementedError(
            "RelationshipFactory is a skeleton stub — implement once "
            "yggdrasil.graph.models.Relationship exists."
        )
