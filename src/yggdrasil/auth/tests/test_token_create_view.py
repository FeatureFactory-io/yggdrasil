"""
Integration tests for TokenCreateView (POST /auth/tokens/create/).

Tests use the Django test client against the real view — no mocks.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from yggdrasil.auth.models import PersonalAccessToken


@pytest.mark.django_db
def test_create_token_stores_hash_not_raw(client, django_user_model):
    """
    Successful POST persists the token and stores only its SHA-256 hash.

    The raw value must appear in the 200 response but NOT equal the
    stored token_hash (i.e. hash is never the raw token).

    :Example:

    POST /auth/tokens/create/ name=ci-bot scope=read-write
    → 200, token stored, raw ≠ token_hash
    """
    user = django_user_model.objects.create_user(username="u", password="p")
    client.force_login(user)

    response = client.post(reverse("auth:token_create"), {"name": "ci-bot", "scope": "read-write"})

    assert response.status_code == 200
    token = PersonalAccessToken.objects.get(user=user, name="ci-bot")
    assert token.scope == "read-write"
    raw = response.context["new_token_raw"]
    assert raw != token.token_hash
    assert len(token.token_hash) == 64


@pytest.mark.django_db
def test_create_token_raw_visible_in_response(client, django_user_model):
    """
    The raw token value appears in the response context exactly once.

    :Example:

    POST → 200, context["new_token_raw"] is set and non-empty
    """
    user = django_user_model.objects.create_user(username="u2", password="p")
    client.force_login(user)

    response = client.post(reverse("auth:token_create"), {"name": "laptop", "scope": "read-only"})

    assert response.status_code == 200
    raw = response.context.get("new_token_raw")
    assert raw is not None
    assert len(raw) > 20


@pytest.mark.django_db
def test_create_token_invalid_scope_returns_400(client, django_user_model):
    """
    POST with an unknown scope value returns 400 and creates no token.

    :Example:

    POST /auth/tokens/create/ name=t scope=super-admin → 400
    """
    user = django_user_model.objects.create_user(username="u3", password="p")
    client.force_login(user)

    response = client.post(reverse("auth:token_create"), {"name": "t", "scope": "super-admin"})

    assert response.status_code == 400
    assert not PersonalAccessToken.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_create_token_blank_name_returns_400(client, django_user_model):
    """
    POST with an empty name returns 400 and creates no token.

    :Example:

    POST /auth/tokens/create/ name= scope=read-only → 400
    """
    user = django_user_model.objects.create_user(username="u4", password="p")
    client.force_login(user)

    response = client.post(reverse("auth:token_create"), {"name": "", "scope": "read-only"})

    assert response.status_code == 400
    assert not PersonalAccessToken.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_create_token_requires_login(client):
    """
    Unauthenticated POST is redirected to login.

    :Example:

    anon → POST /auth/tokens/create/ → 302 → /auth/login/
    """
    response = client.post(reverse("auth:token_create"), {"name": "t", "scope": "read-only"})

    assert response.status_code == 302
    assert "/auth/login/" in response["Location"]


@pytest.mark.django_db
def test_create_token_different_users_isolated(client, django_user_model):
    """
    Tokens created by user_a are not visible in user_b's token list.

    :Example:

    user_a creates token; user_b GETs /auth/tokens/ → user_a's token absent
    """
    user_a = django_user_model.objects.create_user(username="ua", password="p")
    user_b = django_user_model.objects.create_user(username="ub", password="p")
    client.force_login(user_a)
    client.post(reverse("auth:token_create"), {"name": "private-a", "scope": "read-only"})

    client.force_login(user_b)
    response = client.get(reverse("auth:token_list"))

    assert b"private-a" not in response.content
