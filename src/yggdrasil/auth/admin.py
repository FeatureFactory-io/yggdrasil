"""
Django admin registrations for the auth app.

PersonalAccessToken is read-only in admin (no raw token values exposed).
Tokens can be listed and revoked but never created via admin — creation
always goes through TokenService to ensure the raw token is shown to the
user exactly once.
"""

from __future__ import annotations

from typing import ClassVar

from django.contrib import admin

from yggdrasil.auth.models import PersonalAccessToken


@admin.register(PersonalAccessToken)
class PersonalAccessTokenAdmin(admin.ModelAdmin):
    """
    Admin view for PersonalAccessToken.

    Intentionally read-only for the token_hash field.
    Supports revoking (delete) and filtering by user/scope.
    """

    list_display: ClassVar[list[str]] = ["name", "user", "scope", "created_at", "last_used_at"]
    list_filter: ClassVar[list[str]] = ["scope", "created_at"]
    search_fields: ClassVar[list[str]] = ["name", "user__username", "user__email"]
    readonly_fields: ClassVar[list[str]] = ["token_hash", "created_at", "last_used_at"]
    ordering: ClassVar[list[str]] = ["-created_at"]
