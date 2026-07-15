"""
Root pytest conftest.

Django settings are selected via pyproject.toml (DJANGO_SETTINGS_MODULE = "yggdrasil.test_settings").
test_settings.py forces in-memory SQLite — no Docker/Postgres required for unit tests.
"""

from __future__ import annotations

import pytest
from django.test import Client
from tests.fixtures.factories import UserFactory


@pytest.fixture()
def client() -> Client:
    """Unauthenticated Django test client, available to every test."""
    return Client()


@pytest.fixture()
def logged_in_user(db, client: Client):
    """A ``viewer``-role user, created via ``UserFactory`` and logged into ``client``.

    :return: the created :class:`django.contrib.auth.models.User`.

    :Example:

    >>> def test_dashboard_requires_login(client, logged_in_user):
    ...     response = client.get("/dashboard/")
    ...     assert response.status_code == 200
    """
    user = UserFactory(is_viewer=True)
    user.set_password("test-pass-only-1234")
    user.save()
    client.login(username=user.username, password="test-pass-only-1234")
    return user
