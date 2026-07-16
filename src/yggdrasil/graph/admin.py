"""
Django admin for the graph app — Elena's metamodel governance tool.

All six models are registered. Stereotype and Package are the primary
metamodel configuration surfaces (create/edit via admin); Element and
Relationship are readable and searchable but writes go through the
ChangeSet pipeline in production.
"""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from yggdrasil.graph.models import (
    Diagram,
    Element,
    Package,
    Relationship,
    Stereotype,
    YggdrasilModel,
)


@admin.register(YggdrasilModel)
class YggdrasilModelAdmin(admin.ModelAdmin):
    """Admin for top-level architecture models."""

    list_display: ClassVar[list[str]] = ["name", "slug", "metamodel", "owner_group", "created_at"]
    list_filter: ClassVar[list[str]] = ["metamodel"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at"]


@admin.register(Stereotype)
class StereotypeAdmin(admin.ModelAdmin):
    """
    Admin for element and edge type definitions.

    ``property_schema`` and ``allowed_edge_rules`` are JSONB — the
    admin uses Django's default JSON widget. Elena edits these directly
    when customising the C4 metamodel.
    """

    list_display: ClassVar[list[str]] = ["name", "model", "slug", "is_edge"]
    list_filter: ClassVar[list[str]] = ["model", "is_edge"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin for organisational package hierarchy."""

    list_display: ClassVar[list[str]] = ["name", "model", "slug", "parent"]
    list_filter: ClassVar[list[str]] = ["model"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}


@admin.register(Diagram)
class DiagramAdmin(admin.ModelAdmin):
    """Admin for C4 diagram definitions."""

    list_display: ClassVar[list[str]] = ["name", "model", "package", "diagram_type"]
    list_filter: ClassVar[list[str]] = ["model", "diagram_type"]
    search_fields: ClassVar[list[str]] = ["name"]
    readonly_fields: ClassVar[list[str]] = ["layout_data"]


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    """
    Admin for graph elements — primarily read-only in production.

    Elements are created/updated via the ChangeSet pipeline. This admin
    view exists for data inspection, bulk operations (superuser only),
    and seeding C4 default data.
    """

    list_display: ClassVar[list[str]] = [
        "name",
        "model",
        "stereotype",
        "package",
        "health",
        "source",
        "confidence",
    ]
    list_filter: ClassVar[list[str]] = ["model", "stereotype", "package", "health", "source"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at", "confidence"]
    filter_horizontal: ClassVar[list[str]] = ["diagrams"]


@admin.register(Relationship)
class RelationshipAdmin(admin.ModelAdmin):
    """Admin for graph relationships — primarily read-only in production."""

    list_display: ClassVar[list[str]] = ["__str__", "model", "stereotype", "confidence"]
    list_filter: ClassVar[list[str]] = ["model", "stereotype"]
    search_fields: ClassVar[list[str]] = ["source__name", "target__name"]
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at"]
