"""
AutoFixture helper — create test users with sensible defaults (TFK-04).

Use when a test needs a user in a given RBAC role but does not care about
specific field values. Backed by ``UserFactory`` (real DB, no mocks).

``ElementFactory`` / ``RelationshipFactory`` remain stubs until
``yggdrasil.graph.models`` ships — see ``tests/fixtures/factories/model_factories.py``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal

from tests.fixtures.factories import UserFactory

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

logger = logging.getLogger(__name__)

Role = Literal["admin", "architect", "viewer"]
_DEFAULT_PASSWORD = "test-pass-only-1234"

_ROLE_TRAITS: dict[Role, str] = {
    "admin": "is_admin",
    "architect": "is_architect",
    "viewer": "is_viewer",
}


def make_user(role: Role = "viewer", *, password: str = _DEFAULT_PASSWORD) -> AbstractUser:
    """
    Create a user with the given RBAC role via ``UserFactory``.

    :param role: ``admin``, ``architect``, or ``viewer``.
    :param password: login password (test-only default).
    :return: persisted ``User`` instance.
    """
    trait = _ROLE_TRAITS[role]
    user = UserFactory(**{trait: True})
    user.set_password(password)
    user.save()
    logger.info("AutoFixture created user role=%s username=%s", role, user.username)
    return user


def make_admin(*, password: str = _DEFAULT_PASSWORD) -> AbstractUser:
    """Create an admin user (``is_staff`` + ``is_superuser``)."""
    return make_user("admin", password=password)


def make_architect(*, password: str = _DEFAULT_PASSWORD) -> AbstractUser:
    """Create an architect user (``architect`` group)."""
    return make_user("architect", password=password)


def make_viewer(*, password: str = _DEFAULT_PASSWORD) -> AbstractUser:
    """Create a viewer user (``viewer`` group)."""
    return make_user("viewer", password=password)
