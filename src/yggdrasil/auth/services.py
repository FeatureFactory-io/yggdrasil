"""
Auth service layer: token lifecycle and credential verification.

All business logic lives here. Views and MCP tools call services;
neither touches ORM directly (SAO.md §3 — layer separation).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.db.models import QuerySet

    from yggdrasil.auth.models import PersonalAccessToken

logger = logging.getLogger("yggdrasil.auth")

_TOKEN_BYTES = 32  # 256 bits of entropy


class TokenService:
    """
    Create, list, revoke, and authenticate personal access tokens.

    :Example:

    >>> svc = TokenService()
    >>> token, raw = svc.create_token(user, "laptop", "read-write")
    >>> svc.authenticate(raw)  # returns user
    """

    def create_token(
        self,
        user: AbstractBaseUser,
        name: str,
        scope: str,
    ) -> tuple[PersonalAccessToken, str]:
        """
        Create a new hashed token; return the ORM instance and raw value.

        The raw token is the only moment it is visible — callers must
        surface it immediately and discard it.

        :param user: Token owner.
        :param name: Human-readable label (e.g. "laptop-ratatosk").
        :param scope: "read-only" or "read-write".
        :return: ``(PersonalAccessToken instance, raw_token_string)``.
        :raises ValueError: If scope is not a valid choice.
        """
        raise NotImplementedError()

    def revoke_token(self, user: AbstractBaseUser, token_id: int) -> None:
        """
        Permanently delete a token owned by *user*.

        :param user: Must be the token owner (or admin).
        :param token_id: Primary key of the token to delete.
        :raises PermissionError: If the token does not belong to *user*.
        :raises PersonalAccessToken.DoesNotExist: If token not found.
        """
        raise NotImplementedError()

    def list_tokens(self, user: AbstractBaseUser) -> QuerySet[PersonalAccessToken]:
        """
        Return all active tokens for *user*, newest first.

        :param user: Token owner.
        :return: QuerySet of PersonalAccessToken.
        """
        raise NotImplementedError()

    def authenticate(self, raw_token: str) -> AbstractBaseUser | None:
        """
        Verify *raw_token* and return the associated user if valid.

        Called by ``TokenAuthentication.authenticate()``. Updates
        ``last_used_at`` on a cache miss so activity tracking is accurate.

        :param raw_token: The unhashed token string from the request header.
        :return: User if the token is valid and active; ``None`` otherwise.
        """
        raise NotImplementedError()

    # ── private helpers ──────────────────────────────────────────────────────

    def _generate_raw_token(self) -> str:
        """Return a URL-safe random token string of ``_TOKEN_BYTES`` bytes."""
        raise NotImplementedError()

    def _hash_token(self, raw: str) -> str:
        """
        Return the SHA-256 hex digest of *raw*.

        :param raw: Plaintext token.
        :return: 64-char hex string.
        """
        raise NotImplementedError()
