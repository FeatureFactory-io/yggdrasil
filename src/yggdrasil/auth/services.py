"""
Auth service layer: token lifecycle and credential verification.

All business logic lives here. Views and MCP tools call services;
neither touches ORM directly (SAO.md §3 — layer separation).
"""

from __future__ import annotations

import hashlib
import logging
import secrets
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
        surface it immediately and discard it.  The SHA-256 hash is stored;
        the plaintext is never persisted or logged.

        :param user: Token owner.
        :param name: Human-readable label (e.g. "laptop-ratatosk").
        :param scope: "read-only" or "read-write".
        :return: ``(PersonalAccessToken instance, raw_token_string)``.
        :raises ValueError: If scope is not a valid choice or name is blank.

        :Example:

        >>> svc = TokenService()
        >>> token, raw = svc.create_token(user, "laptop", "read-write")
        >>> token.pk is not None
        True
        """
        from yggdrasil.auth.models import PersonalAccessToken

        self._validate_create_params(name, scope)
        raw = self._generate_raw_token()
        token_hash = self._hash_token(raw)
        logger.info(
            "TokenService.create_token | user_pk=%s name=%s scope=%s",
            user.pk,
            name,
            scope,
        )
        token = PersonalAccessToken.objects.create(
            user=user,
            name=name.strip(),
            token_hash=token_hash,
            scope=scope,
        )
        logger.info("TokenService.create_token: created | token_pk=%s", token.pk)
        return token, raw

    def _validate_create_params(self, name: str, scope: str) -> None:
        """
        Validate token name and scope before creation.

        :param name: Token label supplied by the user.
        :param scope: Requested scope string.
        :raises ValueError: If name is blank or scope is not a known value.
        """
        from yggdrasil.auth.models import PersonalAccessToken

        if not name or not name.strip():
            raise ValueError("Token name cannot be blank")
        valid_scopes = {PersonalAccessToken.SCOPE_READ_ONLY, PersonalAccessToken.SCOPE_READ_WRITE}
        if scope not in valid_scopes:
            raise ValueError(f"Invalid scope {scope!r}. Expected one of {sorted(valid_scopes)}")

    def revoke_token(self, user: AbstractBaseUser, token_id: int) -> None:
        """
        Permanently delete a token owned by *user*.

        :param user: Must be the token owner (or admin).
        :param token_id: Primary key of the token to delete.
        :raises PermissionError: If the token does not belong to *user*.
        :raises PersonalAccessToken.DoesNotExist: If token not found.

        :Example:

        >>> svc = TokenService()
        >>> svc.revoke_token(user, token_id=1)  # raises PermissionError if wrong owner
        """
        from yggdrasil.auth.models import PersonalAccessToken

        logger.info("TokenService.revoke_token | user_pk=%s token_id=%s", user.pk, token_id)
        token = PersonalAccessToken.objects.get(pk=token_id)
        if token.user_id != user.pk:
            logger.warning(
                "TokenService.revoke_token: ownership mismatch | user_pk=%s token.user_pk=%s",
                user.pk,
                token.user_id,
            )
            raise PermissionError(f"Token {token_id} does not belong to user {user.pk}")
        token.delete()
        logger.info("TokenService.revoke_token: deleted | token_id=%s", token_id)

    def list_tokens(self, user: AbstractBaseUser) -> QuerySet[PersonalAccessToken]:
        """
        Return all active tokens for *user*, newest first.

        Filters strictly by owner so cross-user token leakage is impossible.

        :param user: Token owner.
        :return: QuerySet of :class:`PersonalAccessToken` ordered by
            ``-created_at``.

        :Example:

        >>> svc = TokenService()
        >>> qs = svc.list_tokens(user)  # returns only user's tokens
        """
        from yggdrasil.auth.models import PersonalAccessToken  # avoid circular at module level

        logger.info("TokenService.list_tokens | user_pk=%s", user.pk)
        return PersonalAccessToken.objects.filter(user=user).order_by("-created_at")

    def authenticate(self, raw_token: str) -> AbstractBaseUser | None:
        """
        Verify *raw_token* and return the associated user if valid.

        Called by ``TokenAuthentication.authenticate()``. Updates
        ``last_used_at`` so activity tracking is accurate.

        :param raw_token: The unhashed token string from the request header.
        :return: User if the token is valid and active; ``None`` otherwise.

        :Example:

        >>> svc = TokenService()
        >>> token, raw = svc.create_token(user, "laptop", "read-write")
        >>> svc.authenticate(raw)  # returns user
        >>> svc.authenticate("bogus")  # returns None
        """
        from django.utils import timezone

        from yggdrasil.auth.models import PersonalAccessToken

        if not raw_token or not raw_token.strip():
            logger.info("TokenService.authenticate: blank token — reject")
            return None
        token_hash = self._hash_token(raw_token.strip())
        try:
            token = PersonalAccessToken.objects.select_related("user").get(token_hash=token_hash)
        except PersonalAccessToken.DoesNotExist:
            logger.warning("TokenService.authenticate: no match for hash prefix=%s", token_hash[:8])
            return None
        PersonalAccessToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        logger.info(
            "TokenService.authenticate: ok | user_pk=%s token_pk=%s scope=%s",
            token.user_id,
            token.pk,
            token.scope,
        )
        return token.user

    # ── private helpers ──────────────────────────────────────────────────────

    def _generate_raw_token(self) -> str:
        """
        Return a URL-safe random token string of ``_TOKEN_BYTES`` bytes.

        :return: 43-char URL-safe base64 string (256 bits of entropy).

        :Example:

        >>> svc = TokenService()
        >>> raw = svc._generate_raw_token()
        >>> len(raw) > 30
        True
        """
        return secrets.token_urlsafe(_TOKEN_BYTES)

    def _hash_token(self, raw: str) -> str:
        """
        Return the SHA-256 hex digest of *raw*.

        :param raw: Plaintext token.
        :return: 64-char hex string.

        :Example:

        >>> svc = TokenService()
        >>> digest = svc._hash_token("abc")
        >>> len(digest)
        64
        """
        return hashlib.sha256(raw.encode()).hexdigest()
