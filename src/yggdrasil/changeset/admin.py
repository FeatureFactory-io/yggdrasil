"""Admin registration for ChangeSet bounded context."""

from typing import ClassVar

from django.contrib import admin

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem, MuninRule


class ChangeSetItemInline(admin.TabularInline):
    model = ChangeSetItem
    extra = 0
    fields = ("order", "op_type", "status", "confidence", "rejection_reason")
    readonly_fields = ("order", "op_type", "confidence")


@admin.register(ChangeSet)
class ChangeSetAdmin(admin.ModelAdmin):
    list_display = ("id", "model", "run_id", "source", "status", "review_mode", "created_at")
    list_filter = ("status", "source", "review_mode", "model")
    inlines: ClassVar = [ChangeSetItemInline]
    readonly_fields = ("created_at", "applied_at")


@admin.register(MuninRule)
class MuninRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "model", "rule_text", "is_active", "created_at")
    list_filter = ("is_active", "model")
    readonly_fields = ("created_at",)
