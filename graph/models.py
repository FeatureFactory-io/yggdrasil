"""Graph domain models — Element, Relationship, Stereotype, Package, Diagram, ChangeSet."""

from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BitemporalModel(models.Model):
    """Append-only validity window for graph facts."""

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ProvenanceMixin(models.Model):
    source = models.CharField(max_length=64, default="manual")  # manual, ratatosk, import
    ratatosk_run_id = models.CharField(max_length=64, blank=True, default="")
    discovered_at = models.DateTimeField(null=True, blank=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)
    confidence = models.FloatField(default=1.0)  # 0.0–1.0

    class Meta:
        abstract = True


class Stereotype(TimeStampedModel):
    """Metamodel definition: property schema and allowed edge rules."""

    name = models.CharField(max_length=128, unique=True)
    kind = models.CharField(
        max_length=16,
        choices=[("vertex", "Vertex"), ("edge", "Edge")],
        default="vertex",
    )
    property_schema = models.JSONField(default=dict, blank=True)
    allowed_edges = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:
        return self.name


class Package(TimeStampedModel):
    """View root / container in the metamodel."""

    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="children"
    )

    def __str__(self) -> str:
        return self.name


class Element(BitemporalModel, ProvenanceMixin, TimeStampedModel):
    """Vertex in the organizational graph."""

    name = models.CharField(max_length=256)
    stereotype = models.ForeignKey(Stereotype, on_delete=models.PROTECT, related_name="elements")
    package = models.ForeignKey(
        Package, on_delete=models.SET_NULL, null=True, blank=True, related_name="elements"
    )
    properties = models.JSONField(default=dict, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_elements",
    )

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.stereotype.name})"


class Relationship(BitemporalModel, ProvenanceMixin, TimeStampedModel):
    """Edge between two elements."""

    from_element = models.ForeignKey(
        Element, on_delete=models.CASCADE, related_name="outgoing"
    )
    to_element = models.ForeignKey(
        Element, on_delete=models.CASCADE, related_name="incoming"
    )
    stereotype = models.ForeignKey(
        Stereotype, on_delete=models.PROTECT, related_name="relationships"
    )
    properties = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["from_element", "to_element"]),
            models.Index(fields=["valid_from", "valid_to"]),
        ]

    def __str__(self) -> str:
        return f"{self.from_element} -[{self.stereotype}]-> {self.to_element}"


class Diagram(TimeStampedModel):
    """Cytoscape presentation layout for a package."""

    name = models.CharField(max_length=128)
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name="diagrams")
    cytoscape_layout = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return self.name


class ChangeSetStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    APPLIED = "applied", "Applied"
    REJECTED = "rejected", "Rejected"
    PARTIAL = "partial", "Partial"


class ChangeSet(TimeStampedModel):
    """Staged writes from Ratatosk awaiting review."""

    run_id = models.CharField(max_length=64, unique=True)
    source = models.CharField(max_length=64, default="ratatosk")
    status = models.CharField(
        max_length=16, choices=ChangeSetStatus.choices, default=ChangeSetStatus.PENDING
    )
    items = models.JSONField(default=list)  # proposed adds/updates/deletes
    confidence_min = models.FloatField(default=0.0)
    confidence_max = models.FloatField(default=1.0)
    submitted_by = models.CharField(max_length=128, blank=True, default="")

    def __str__(self) -> str:
        return f"ChangeSet {self.run_id} ({self.status})"
