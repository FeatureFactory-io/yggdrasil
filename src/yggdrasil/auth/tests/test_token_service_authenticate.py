"""Unit tests for TokenService.authenticate."""

from __future__ import annotations

import logging

import pytest
from rest_framework.test import APIRequestFactory
from tests.support.log_story import assert_log_story

from yggdrasil.auth.authentication import TokenAuthentication
from yggdrasil.auth.services import TokenService

_AUTH_LOG = "yggdrasil.auth"


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


@pytest.mark.django_db
def test_authenticate_log_story_happy(django_user_model, caplog):
    """Valid token logs last_used_at update and exit identifiers, never the raw token."""
    user = django_user_model.objects.create_user(username="tok_story", password="p")
    svc = TokenService()
    token, raw = svc.create_token(user, "laptop", "read-write")
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        found = svc.authenticate(raw)
    assert found is not None
    assert_log_story(
        caplog,
        where="TokenService.authenticate",
        beats={
            "entry": [" | entry | ", "token_len="],
            "processing": [" | processing | ", "last_used_at updated"],
            "exit": [" | exit | ", "user_pk=", "token_pk=", "scope="],
        },
    )
    assert raw not in caplog.text


@pytest.mark.django_db
def test_authenticate_log_story_reject(caplog):
    """Unknown token logs an error beat with hash prefix only."""
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        found = TokenService().authenticate("not-a-real-token")
    assert found is None
    assert_log_story(
        caplog,
        where="TokenService.authenticate",
        beats={
            "entry": [" | entry | ", "token_len="],
            "error": [" | error | ", "reason=no_match", "hash_prefix="],
        },
    )
    assert "not-a-real-token" not in caplog.text


@pytest.mark.django_db
def test_authenticate_blank_token_log_story_reject(caplog):
    """Blank token is rejected with an explicit branch reason."""
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        found = TokenService().authenticate("")
    assert found is None
    assert_log_story(
        caplog,
        where="TokenService.authenticate",
        beats={
            "entry": [" | entry | ", "token_len="],
            "branch": [" | branch | ", "reason=blank_token"],
        },
    )


@pytest.mark.django_db
def test_create_token_log_story_happy(django_user_model, caplog):
    """create_token logs owner/name/scope and token_pk, never the raw secret."""
    user = django_user_model.objects.create_user(username="tok_create_story", password="p")
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        token, raw = TokenService().create_token(user, "laptop", "read-write")
    assert token.pk is not None
    assert_log_story(
        caplog,
        where="TokenService.create_token",
        beats={
            "entry": [" | entry | ", "user_pk=", "name=laptop", "scope=read-write"],
            "validation": [" | validation | ", "status=ok"],
            "processing": [" | processing | ", "hash_prefix="],
            "exit": [" | exit | ", "token_pk="],
        },
    )
    assert raw not in caplog.text


@pytest.mark.django_db
def test_create_token_log_story_reject_blank_name(django_user_model, caplog):
    """Blank name logs validation reason=blank_name."""
    user = django_user_model.objects.create_user(username="tok_blank_name", password="p")
    with (
        caplog.at_level(logging.INFO, logger=_AUTH_LOG),
        pytest.raises(ValueError),
    ):
        TokenService().create_token(user, "  ", "read-only")
    assert_log_story(
        caplog,
        where="TokenService._validate_create_params",
        beats={"validation": [" | validation | ", "reason=blank_name"]},
    )


@pytest.mark.django_db
def test_create_token_log_story_reject_invalid_scope(django_user_model, caplog):
    """Unknown scope logs validation reason=invalid_scope."""
    user = django_user_model.objects.create_user(username="tok_bad_scope", password="p")
    with (
        caplog.at_level(logging.INFO, logger=_AUTH_LOG),
        pytest.raises(ValueError),
    ):
        TokenService().create_token(user, "ci-bot", "super-admin")
    assert_log_story(
        caplog,
        where="TokenService._validate_create_params",
        beats={"validation": [" | validation | ", "reason=invalid_scope", "scope=super-admin"]},
    )


@pytest.mark.django_db
def test_list_tokens_log_story_happy(django_user_model, caplog):
    """list_tokens logs why it filters to the owner."""
    user = django_user_model.objects.create_user(username="tok_list_story", password="p")
    TokenService().create_token(user, "laptop", "read-only")
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        tokens = TokenService().list_tokens(user)
        assert tokens.count() == 1
    assert_log_story(
        caplog,
        where="TokenService.list_tokens",
        beats={
            "entry": [" | entry | ", "user_pk="],
            "branch": [" | branch | ", "reason=owner_filter"],
            "exit": [" | exit | ", "token_count="],
        },
    )


def test_token_authentication_placeholder_log_story(caplog):
    """Placeholder authenticator logs why it always returns None."""
    request = APIRequestFactory().get("/")
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        result = TokenAuthentication().authenticate(request)
    assert result is None
    assert_log_story(
        caplog,
        where="TokenAuthentication.authenticate",
        beats={
            "entry": [" | entry | ", "has_authorization="],
            "branch": [" | branch | ", "reason=placeholder_unimplemented"],
        },
    )
