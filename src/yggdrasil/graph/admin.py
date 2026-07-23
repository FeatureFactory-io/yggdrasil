"""
Django admin for the graph app — Metamodel governance (MVP surface).

Metamodel, Stereotype and Package are the type-catalog surfaces.
Element and Relationship are readable/searchable; production writes go
through the ChangeSet pipeline.
"""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from yggdrasil.graph.models import (
    Diagram,
    Element,
    Metamodel,
    Package,
    Relationship,
    Stereotype,
    YggdrasilModel,
)


@admin.register(Metamodel)
class MetamodelAdmin(admin.ModelAdmin):
    """Admin for type catalogs (Stereotypes + Packages)."""

    list_display: ClassVar[list[str]] = ["name", "slug", "created_at"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at"]


@admin.register(YggdrasilModel)
class YggdrasilModelAdmin(admin.ModelAdmin):
    """Admin for top-level architecture models (metamodel immutable after create)."""

    list_display: ClassVar[list[str]] = ["name", "slug", "metamodel", "owner_group", "created_at"]
    list_filter: ClassVar[list[str]] = ["metamodel"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}
    readonly_fields: ClassVar[list[str]] = ["created_at", "updated_at"]

    def get_readonly_fields(self, request, obj=None):
        """Lock metamodel on change forms."""
        fields = list(self.readonly_fields)
        if obj is not None:
            fields.append("metamodel")
        return fields


@admin.register(Stereotype)
class StereotypeAdmin(admin.ModelAdmin):
    """
    Admin for element and edge type definitions on a Metamodel.

    ``property_schema`` and ``allowed_edge_rules`` are JSONB — the
    admin uses Django's default JSON widget.
    """

    list_display: ClassVar[list[str]] = ["name", "metamodel", "slug", "is_edge"]
    list_filter: ClassVar[list[str]] = ["metamodel", "is_edge"]
    search_fields: ClassVar[list[str]] = ["name", "slug", "description"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}
    fields: ClassVar[list[str]] = [
        "metamodel",
        "name",
        "slug",
        "description",
        "is_edge",
        "property_schema",
        "allowed_edge_rules",
        "color",
        "icon",
    ]


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    """Admin for metamodel package hierarchy."""

    list_display: ClassVar[list[str]] = ["name", "metamodel", "slug", "parent"]
    list_filter: ClassVar[list[str]] = ["metamodel"]
    search_fields: ClassVar[list[str]] = ["name", "slug"]
    prepopulated_fields: ClassVar[dict[str, tuple[str, ...]]] = {"slug": ("name",)}


@admin.register(Diagram)
class DiagramAdmin(admin.ModelAdmin):
    """Admin for C4 diagram instances on a Model."""

    list_display: ClassVar[list[str]] = ["name", "model", "package", "diagram_type"]
    list_filter: ClassVar[list[str]] = ["model", "diagram_type"]
    search_fields: ClassVar[list[str]] = ["name"]
    readonly_fields: ClassVar[list[str]] = ["layout_data"]


@admin.register(Element)
class ElementAdmin(admin.ModelAdmin):
    """
    Admin for graph elements — primarily read-only in production.

    Elements are created/updated via the ChangeSet pipeline. This admin
    view exists for data inspection and bulk operations (superuser only).
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
