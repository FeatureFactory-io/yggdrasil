"""Unit tests for TokenService.authenticate."""

from __future__ import annotations

import pytest

from yggdrasil.auth.services import TokenService


@pytest.mark.django_db
def test_authenticate_returns_user_for_valid_token(django_user_model):
    """Valid raw token resolves to the owning user."""
    user = django_user_model.objects.create_user(username="tok_user", password="p")
    svc = TokenService()
    _token, raw = svc.create_token(user, "laptop", "read-write")

    found = svc.authenticate(raw)

    assert found is not None
    assert found.pk == user.pk


@pytest.mark.django_db
def test_authenticate_rejects_bogus_token(django_user_model):
    """Unknown raw token returns None."""
    django_user_model.objects.create_user(username="tok_user2", password="p")
    found = TokenService().authenticate("not-a-real-token")
    assert found is None


@pytest.mark.django_db
def test_authenticate_rejects_blank_token():
    """Blank / whitespace token returns None without querying."""
    assert TokenService().authenticate("") is None
    assert TokenService().authenticate("   ") is None
