"""
Integration tests for TokenRevokeView (POST /auth/tokens/<id>/revoke/).

Tests use the Django test client against the real view — no mocks.
"""

from __future__ import annotations

import logging

import pytest
from django.urls import reverse
from tests.support.log_story import assert_log_story

from yggdrasil.auth.models import PersonalAccessToken

_AUTH_LOG = "yggdrasil.auth"


@pytest.mark.django_db
def test_revoke_own_token_succeeds(client, django_user_model):
    """
    Authenticated POST to revoke an owned token returns 302 and deletes it.

    :Example:

    force_login → POST /auth/tokens/1/revoke/ → 302, token deleted
    """
    user = django_user_model.objects.create_user(username="u", password="p")
    token = PersonalAccessToken.objects.create(
        user=user, name="my-token", token_hash="abc123", scope="read-only"
    )
    client.force_login(user)

    response = client.post(reverse("auth:token_revoke", args=[token.pk]))

    assert response.status_code == 302
    assert response["Location"] == reverse("auth:token_list")
    assert not PersonalAccessToken.objects.filter(pk=token.pk).exists()


@pytest.mark.django_db
def test_revoke_other_users_token_returns_403(client, django_user_model):
    """
    Attempting to revoke another user's token returns 403 and leaves it intact.

    Verifies the ownership check in TokenService.revoke_token cannot be
    bypassed by supplying a known token PK.

    :Example:

    attacker force_login → POST /auth/tokens/<owner_token_pk>/revoke/ → 403
    """
    owner = django_user_model.objects.create_user(username="owner", password="p")
    attacker = django_user_model.objects.create_user(username="attacker", password="p")
    token = PersonalAccessToken.objects.create(
        user=owner, name="owner-token", token_hash="def456", scope="read-only"
    )
    client.force_login(attacker)

    response = client.post(reverse("auth:token_revoke", args=[token.pk]))

    assert response.status_code == 403
    assert PersonalAccessToken.objects.filter(pk=token.pk).exists()


@pytest.mark.django_db
def test_revoke_nonexistent_token_returns_404(client, django_user_model):
    """
    POST to revoke a non-existent token PK returns 404.

    :Example:

    force_login → POST /auth/tokens/9999/revoke/ → 404
    """
    user = django_user_model.objects.create_user(username="u2", password="p")
    client.force_login(user)

    response = client.post(reverse("auth:token_revoke", args=[9999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_revoke_requires_post(client, django_user_model):
    """
    GET to revoke endpoint returns 405 Method Not Allowed (CSRF safety).

    :Example:

    force_login → GET /auth/tokens/1/revoke/ → 405
    """
    user = django_user_model.objects.create_user(username="u3", password="p")
    token = PersonalAccessToken.objects.create(
        user=user, name="t", token_hash="ghi789", scope="read-only"
    )
    client.force_login(user)

    response = client.get(reverse("auth:token_revoke", args=[token.pk]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_revoke_requires_login(client, django_user_model):
    """
    Unauthenticated POST is redirected to login.

    :Example:

    anon → POST /auth/tokens/1/revoke/ → 302 → /auth/login/
    """
    user = django_user_model.objects.create_user(username="u4", password="p")
    token = PersonalAccessToken.objects.create(
        user=user, name="t2", token_hash="jkl012", scope="read-only"
    )

    response = client.post(reverse("auth:token_revoke", args=[token.pk]))

    assert response.status_code == 302
    assert "/auth/login/" in response["Location"]
    assert PersonalAccessToken.objects.filter(pk=token.pk).exists()


@pytest.mark.django_db
def test_revoke_log_story_happy(client, django_user_model, caplog):
    """Owner revoke logs processing/delete and view exit."""
    user = django_user_model.objects.create_user(username="u_revoke_story", password="p")
    token = PersonalAccessToken.objects.create(
        user=user, name="my-token", token_hash="abc123story", scope="read-only"
    )
    client.force_login(user)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.post(reverse("auth:token_revoke", args=[token.pk]))
    assert response.status_code == 302
    assert_log_story(
        caplog,
        where="TokenRevokeView.post",
        beats={
            "entry": [" | entry | ", "user_pk=", "token_id="],
            "exit": [" | exit | ", "revoked", "token_id="],
        },
    )
    assert_log_story(
        caplog,
        where="TokenService.revoke_token",
        beats={
            "entry": [" | entry | ", "user_pk=", "token_id="],
            "processing": [" | processing | ", "deleting", "token_id="],
            "exit": [" | exit | ", "deleted", "token_id="],
        },
    )


@pytest.mark.django_db
def test_revoke_log_story_reject_ownership(client, django_user_model, caplog):
    """Cross-user revoke logs ownership_denied / ownership_mismatch reasons."""
    owner = django_user_model.objects.create_user(username="owner_story", password="p")
    attacker = django_user_model.objects.create_user(username="attacker_story", password="p")
    token = PersonalAccessToken.objects.create(
        user=owner, name="owner-token", token_hash="def456story", scope="read-only"
    )
    client.force_login(attacker)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.post(reverse("auth:token_revoke", args=[token.pk]))
    assert response.status_code == 403
    assert_log_story(
        caplog,
        where="TokenRevokeView.post",
        beats={"branch": [" | branch | ", "reason=ownership_denied", "token_id="]},
    )
    assert_log_story(
        caplog,
        where="TokenService.revoke_token",
        beats={"branch": [" | branch | ", "reason=ownership_mismatch"]},
        level="WARNING",
    )


@pytest.mark.django_db
def test_revoke_log_story_reject_not_found(client, django_user_model, caplog):
    """Missing token logs not_found on both the view and the service."""
    user = django_user_model.objects.create_user(username="u_revoke_404", password="p")
    client.force_login(user)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.post(reverse("auth:token_revoke", args=[9999]))
    assert response.status_code == 404
    assert_log_story(
        caplog,
        where="TokenRevokeView.post",
        beats={"branch": [" | branch | ", "reason=not_found", "token_id=9999"]},
    )
    assert_log_story(
        caplog,
        where="TokenService.revoke_token",
        beats={"error": [" | error | ", "reason=not_found", "token_id=9999"]},
    )
