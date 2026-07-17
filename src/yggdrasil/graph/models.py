"""
Core graph domain models: the Yggdrasil knowledge graph.

Bounded context: `graph` (SAO.md §1).
Dependency rules: `graph` has no inbound imports from other Yggdrasil apps.
All writes go through the ChangeSet pipeline (SAO.md §1, §4).

JSONB columns (SAO.md §4):
  - Element.properties       — stereotype-driven flexible attributes
  - Relationship.properties  — edge-level flexible attributes
  - Stereotype.property_schema    — JSON Schema for property validation
  - Stereotype.allowed_edge_rules — permitted outbound edge stereotype slugs
"""

from __future__ import annotations

import logging
from typing import ClassVar

from django.contrib.auth.models import Group
from django.db import models
from django.utils.text import slugify

logger = logging.getLogger("yggdrasil.graph")


class YggdrasilModel(models.Model):
    """
    A named architecture knowledge-graph model (e.g. "Yggdrasil").

    Each model has one metamodel (currently C4 only for MVP) and is
    owned by a RBAC group. All Elements, Relationships, Stereotypes,
    Packages and Diagrams belong to exactly one YggdrasilModel.

    :Example:

    >>> model = YggdrasilModel(name="Yggdrasil", metamodel="c4")
    """

    METAMODEL_C4 = "c4"
    METAMODEL_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (METAMODEL_C4, "C4"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    metamodel = models.CharField(max_length=50, choices=METAMODEL_CHOICES, default=METAMODEL_C4)
    owner_group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="owned_models",
        null=True,
        blank=True,
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]
        verbose_name = "Model"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Stereotype(models.Model):
    """
    An element or edge type definition within a metamodel.

    For C4: System, Container, Component, Person, External (element
    stereotypes); calls, depends_on, uses (edge stereotypes).

    ``property_schema`` (JSONB) holds a JSON Schema definition that
    validates ``Element.properties``. ``allowed_edge_rules`` (JSONB) is
    a list of edge stereotype slugs permitted from this node type.

    :Example:

    >>> st = Stereotype(model=m, name="Container", slug="container",
    ...     property_schema={"type": "object", "properties": {"version": {"type": "string"}}})
    """

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="stereotypes",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    is_edge = models.BooleanField(default=False)
    property_schema = models.JSONField(default=dict)
    allowed_edge_rules = models.JSONField(default=list)
    color = models.CharField(max_length=30, blank=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together: ClassVar[list[tuple[str, str]]] = [("model", "slug")]
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.model.slug}/{self.name}"


class Package(models.Model):
    """
    Organisational grouping for elements within a model.

    C4 default packages: Context, Technology, Application, Code.
    Packages are hierarchical (``parent`` is self-referential).

    :Example:

    >>> pkg = Package(model=m, name="Technology", slug="technology")
    """

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="packages",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together: ClassVar[list[tuple[str, str]]] = [("model", "slug")]
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.model.slug}/{self.slug}"


class Diagram(models.Model):
    """
    A named C4 diagram within a package.

    ``layout_data`` (JSONB) stores Cytoscape.js node positions so the
    layout editor can restore element positions between sessions.

    :Example:

    >>> d = Diagram(model=m, package=tech_pkg, name="Container Diagram", diagram_type="container")
    """

    TYPE_CONTEXT = "context"
    TYPE_CONTAINER = "container"
    TYPE_COMPONENT = "component"
    TYPE_CODE = "code"
    TYPE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (TYPE_CONTEXT, "Context"),
        (TYPE_CONTAINER, "Container"),
        (TYPE_COMPONENT, "Component"),
        (TYPE_CODE, "Code"),
    ]

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="diagrams",
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="diagrams",
    )
    name = models.CharField(max_length=200)
    diagram_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    layout_data = models.JSONField(default=dict)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.package}/{self.name}"


class Element(models.Model):
    """
    A node in the architecture knowledge graph.

    ``properties`` (JSONB) holds stereotype-driven flexible attributes
    validated against ``Stereotype.property_schema`` at write time (via
    the ChangeSet pipeline — not at ORM level).

    ``confidence`` is a 0.0-1.0 float set by Ratatosk during extraction.
    Human-created elements default to 1.0.

    :Example:

    >>> e = Element(model=m, name="Payment API", stereotype=container_st,
    ...     package=tech_pkg, properties={"version": "2.3.1"})
    """

    SOURCE_RATATOSK = "ratatosk"
    SOURCE_HUMAN = "human"
    SOURCE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (SOURCE_RATATOSK, "Ratatosk"),
        (SOURCE_HUMAN, "Human"),
    ]
    HEALTH_GREEN = "green"
    HEALTH_YELLOW = "yellow"
    HEALTH_RED = "red"
    HEALTH_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (HEALTH_GREEN, "Green"),
        (HEALTH_YELLOW, "Yellow"),
        (HEALTH_RED, "Red"),
    ]

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="elements",
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    stereotype = models.ForeignKey(
        Stereotype,
        on_delete=models.PROTECT,
        related_name="elements",
        limit_choices_to={"is_edge": False},
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="elements",
    )
    diagrams = models.ManyToManyField(Diagram, blank=True, related_name="elements")
    properties = models.JSONField(default=dict)
    owner = models.CharField(max_length=200, blank=True)
    health = models.CharField(max_length=20, choices=HEALTH_CHOICES, default=HEALTH_GREEN)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_HUMAN)
    confidence = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together: ClassVar[list[tuple[str, str]]] = [("model", "slug")]
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.model.slug}/{self.name}"


class Relationship(models.Model):
    """
    A directed edge between two Elements in the same model.

    ``properties`` (JSONB) holds edge-level flexible attributes.
    ``stereotype`` must be an edge stereotype (``is_edge=True``).

    :Example:

    >>> r = Relationship(model=m, source=payment_api, target=db,
    ...     stereotype=depends_on_st, properties={"label": "reads from"})
    """

    model = models.ForeignKey(
        YggdrasilModel,
        on_delete=models.CASCADE,
        related_name="relationships",
    )
    source = models.ForeignKey(
        Element,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target = models.ForeignKey(
        Element,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    stereotype = models.ForeignKey(
        Stereotype,
        on_delete=models.PROTECT,
        related_name="relationships",
        limit_choices_to={"is_edge": True},
    )
    properties = models.JSONField(default=dict)
    confidence = models.FloatField(default=1.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source} → {self.target} [{self.stereotype.slug}]"
