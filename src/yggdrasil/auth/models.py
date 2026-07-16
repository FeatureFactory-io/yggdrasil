"""
Auth models: PersonalAccessToken for CLI and MCP authentication.

All token values are stored as SHA-256 hashes; the raw token is shown once
on creation and never persisted. Scope is stored as a plain string
("read-only" | "read-write") — fine-grained RBAC lives in the group model.
"""

from __future__ import annotations

import logging
from typing import ClassVar

from django.contrib.auth import get_user_model
from django.db import models

logger = logging.getLogger("yggdrasil.auth")

User = get_user_model()


class PersonalAccessToken(models.Model):
    """
    A hashed personal access token bound to a single user.

    :Example:

    >>> service = TokenService()
    >>> token, raw = service.create_token(user, name="laptop-ratatosk", scope="read-write")
    >>> token.pk  # raw token shown once and discarded
    1
    """

    SCOPE_READ_ONLY = "read-only"
    SCOPE_READ_WRITE = "read-write"
    SCOPE_CHOICES: ClassVar[list[tuple[str, str]]] = [
        (SCOPE_READ_ONLY, "Read-only"),
        (SCOPE_READ_WRITE, "Read-write"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="access_tokens")
    name = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_READ_ONLY)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering: ClassVar[list[str]] = ["-created_at"]
        verbose_name = "Personal Access Token"

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"
