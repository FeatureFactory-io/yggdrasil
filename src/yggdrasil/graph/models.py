"""
Core graph domain models: the Yggdrasil knowledge graph.

Bounded context: `graph` (SAO.md §1).
Dependency rules: `graph` has no inbound imports from other Yggdrasil apps.
All writes go through the ChangeSet pipeline (SAO.md §1, §4).

Layering:
  - Metamodel — type catalog (Stereotypes, Packages)
  - Model — instance graph (Elements, Relationships, Diagrams), immutable FK to Metamodel

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
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

logger = logging.getLogger("yggdrasil.graph")

# Canonical C4 catalog seeded onto Metamodel slug=c4 (admin / data migration).
# Each entry carries the guidance Ratatosk injects into the LLM — not just names.
C4_ELEMENT_STEREOTYPE_SPECS: tuple[dict, ...] = (
    {
        "name": "System",
        "description": (
            "A software system that delivers value to users. "
            "Use for the system-under-study or a major peer system at Context level."
        ),
        "property_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "criticality": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        },
        "allowed_edge_rules": ["uses", "calls", "depends_on"],
    },
    {
        "name": "Container",
        "description": (
            "A deployable/runnable unit: application, API service, database, "
            "message bus, or similar. Prefer Container for services and datastores."
        ),
        "property_schema": {
            "type": "object",
            "properties": {
                "technology": {"type": "string"},
                "version": {"type": "string"},
                "owner": {"type": "string"},
            },
        },
        "allowed_edge_rules": ["calls", "depends_on", "uses"],
    },
    {
        "name": "Component",
        "description": (
            "An internal building block inside a Container: module, domain package, "
            "or library. Do not use for standalone deployables."
        ),
        "property_schema": {
            "type": "object",
            "properties": {
                "language": {"type": "string"},
                "owner": {"type": "string"},
            },
        },
        "allowed_edge_rules": ["depends_on", "uses", "calls"],
    },
    {
        "name": "Person",
        "description": "A human actor or role that interacts with a System.",
        "property_schema": {
            "type": "object",
            "properties": {"role": {"type": "string"}},
        },
        "allowed_edge_rules": ["uses"],
    },
    {
        "name": "External",
        "description": (
            "An external system or SaaS outside the organisation's control "
            "(payment gateway, IdP, third-party API)."
        ),
        "property_schema": {
            "type": "object",
            "properties": {"vendor": {"type": "string"}},
        },
        "allowed_edge_rules": ["calls", "uses"],
    },
)
C4_EDGE_STEREOTYPE_SPECS: tuple[dict, ...] = (
    {
        "name": "calls",
        "description": "Synchronous or request/response invocation from source to target.",
        "property_schema": {
            "type": "object",
            "properties": {"protocol": {"type": "string"}},
        },
    },
    {
        "name": "depends_on",
        "description": "Structural or runtime dependency (library, datastore, queue).",
        "property_schema": {
            "type": "object",
            "properties": {"strength": {"type": "string", "enum": ["weak", "strong"]}},
        },
    },
    {
        "name": "uses",
        "description": "Person or System uses another System/Container as a capability.",
        "property_schema": {"type": "object", "properties": {}},
    },
)
C4_PACKAGE_SPECS: tuple[dict, ...] = (
    {
        "name": "Context",
        "description": "System context view: people, systems, and external actors.",
    },
    {
        "name": "Technology",
        "description": "Containers and infrastructure that realise the system.",
    },
    {
        "name": "Application",
        "description": "Application/domain components inside containers.",
    },
    {
        "name": "Code",
        "description": "Code-level elements when modelled (classes, modules).",
    },
)


class Metamodel(models.Model):
    """
    A named type catalog (convention) that constrains Models.

    Owns Stereotypes and Packages. Ratatosk loads this ontology by slug
    as LLM guidance — it does not invent catalog rows.

    :Example:

    >>> mm = Metamodel(name="C4", slug="c4")
    """

    SLUG_C4 = "c4"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class YggdrasilModel(models.Model):
    """
    A named architecture knowledge-graph model (e.g. "Yggdrasil").

    Each model is bound to exactly one Metamodel (immutable after create)
    and owned by an RBAC group. Elements, Relationships and Diagrams
    belong to the Model; Stereotypes and Packages belong to its Metamodel.

    :Example:

    >>> mm = Metamodel.objects.get(slug="c4")
    >>> model = YggdrasilModel(name="Yggdrasil", metamodel=mm)
    """

    # Kept for call-site convenience (slug of the seeded C4 Metamodel).
    METAMODEL_C4 = Metamodel.SLUG_C4

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    metamodel = models.ForeignKey(
        Metamodel,
        on_delete=models.PROTECT,
        related_name="models",
    )
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
        if self.pk:
            previous = (
                YggdrasilModel.objects.filter(pk=self.pk)
                .values_list("metamodel_id", flat=True)
                .first()
            )
            if previous is not None and previous != self.metamodel_id:
                logger.warning(
                    "YggdrasilModel.save | refused metamodel change | model=%s from=%s to=%s",
                    self.slug,
                    previous,
                    self.metamodel_id,
                )
                raise ValidationError(
                    {"metamodel": "Metamodel cannot be changed after the Model is created."}
                )
        super().save(*args, **kwargs)


class Stereotype(models.Model):
    """
    An element or edge type definition within a Metamodel.

    For C4: System, Container, Component, Person, External (element
    stereotypes); calls, depends_on, uses (edge stereotypes).

    ``property_schema`` (JSONB) holds a JSON Schema definition that
    validates ``Element.properties``. ``allowed_edge_rules`` (JSONB) is
    a list of edge stereotype slugs permitted from this node type.

    :Example:

    >>> st = Stereotype(metamodel=mm, name="Container", slug="container",
    ...     property_schema={"type": "object", "properties": {"version": {"type": "string"}}})
    """

    metamodel = models.ForeignKey(
        Metamodel,
        on_delete=models.CASCADE,
        related_name="stereotypes",
    )
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    description = models.TextField(
        blank=True,
        help_text="Guidance for humans and Ratatosk LLM: when to use this stereotype.",
    )
    is_edge = models.BooleanField(default=False)
    property_schema = models.JSONField(default=dict)
    allowed_edge_rules = models.JSONField(default=list)
    color = models.CharField(max_length=30, blank=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together: ClassVar[list[tuple[str, str]]] = [("metamodel", "slug")]
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.metamodel.slug}/{self.name}"


class Package(models.Model):
    """
    Organisational grouping defined by a Metamodel.

    C4 default packages: Context, Technology, Application, Code.
    Packages are hierarchical (``parent`` is self-referential).

    :Example:

    >>> pkg = Package(metamodel=mm, name="Technology", slug="technology")
    """

    metamodel = models.ForeignKey(
        Metamodel,
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
        unique_together: ClassVar[list[tuple[str, str]]] = [("metamodel", "slug")]
        ordering: ClassVar[list[str]] = ["name"]

    def __str__(self) -> str:
        return f"{self.metamodel.slug}/{self.slug}"


class Diagram(models.Model):
    """
    A named C4 diagram instance within a Model.

    ``layout_data`` (JSONB) stores Cytoscape.js node positions so the
    layout editor can restore element positions between sessions.
    Diagram *types* are constrained by the Metamodel profile; instances
    live on the Model.

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


def ensure_c4_metamodel() -> Metamodel:
    """
    Ensure Metamodel ``c4`` exists with canonical Stereotypes and Packages.

    Idempotent. Refreshes description / property_schema / allowed_edge_rules
    so Ratatosk LLM guidance stays complete even on older rows.

    :return: The C4 Metamodel instance.
    """
    mm, created = Metamodel.objects.get_or_create(
        slug=Metamodel.SLUG_C4,
        defaults={
            "name": "C4",
            "description": (
                "C4 architecture metamodel. Classify software landscape into "
                "Person, System, Container, Component, External; relate them with "
                "calls, depends_on, uses; place them in Context, Technology, "
                "Application, or Code packages."
            ),
        },
    )
    if created:
        logger.info("ensure_c4_metamodel | created Metamodel slug=c4")
    for spec in C4_ELEMENT_STEREOTYPE_SPECS:
        _upsert_stereotype(mm, spec, is_edge=False)
    for spec in C4_EDGE_STEREOTYPE_SPECS:
        _upsert_stereotype(mm, spec, is_edge=True)
    for spec in C4_PACKAGE_SPECS:
        _upsert_package(mm, spec)
    logger.info(
        "ensure_c4_metamodel | stereotypes=%s packages=%s",
        mm.stereotypes.count(),
        mm.packages.count(),
    )
    return mm


def _upsert_stereotype(mm: Metamodel, spec: dict, *, is_edge: bool) -> Stereotype:
    """Create or refresh a Stereotype from a C4 seed spec."""
    slug = slugify(spec["name"])
    st, _ = Stereotype.objects.get_or_create(
        metamodel=mm,
        slug=slug,
        defaults={
            "name": spec["name"],
            "description": spec.get("description") or "",
            "is_edge": is_edge,
            "property_schema": spec.get("property_schema") or {},
            "allowed_edge_rules": spec.get("allowed_edge_rules") or [],
        },
    )
    # Refresh guidance fields so older bare rows become usable for the LLM.
    st.name = spec["name"]
    st.description = spec.get("description") or ""
    st.is_edge = is_edge
    st.property_schema = spec.get("property_schema") or {}
    st.allowed_edge_rules = spec.get("allowed_edge_rules") or []
    st.save(
        update_fields=[
            "name",
            "description",
            "is_edge",
            "property_schema",
            "allowed_edge_rules",
        ]
    )
    return st


def _upsert_package(mm: Metamodel, spec: dict) -> Package:
    """Create or refresh a Package from a C4 seed spec."""
    slug = slugify(spec["name"])
    pkg, _ = Package.objects.get_or_create(
        metamodel=mm,
        slug=slug,
        defaults={"name": spec["name"], "description": spec.get("description") or ""},
    )
    pkg.name = spec["name"]
    pkg.description = spec.get("description") or ""
    pkg.save(update_fields=["name", "description"])
    return pkg
