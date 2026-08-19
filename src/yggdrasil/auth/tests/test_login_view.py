"""
Integration tests for LoginView (GET /auth/login/).

Tests use the Django test client against the real view — no mocks.
"""

from __future__ import annotations

import logging

import pytest
from django.urls import reverse
from tests.support.log_story import assert_log_story

_AUTH_LOG = "yggdrasil.auth"


@pytest.mark.django_db
def test_login_page_renders(client):
    """
    Unauthenticated GET /auth/login/ returns 200 with required testids.

    :Example:

    GET /auth/login/ → 200, body contains data-testid="auth-login-page"
    """
    response = client.get(reverse("auth:login"))
    assert response.status_code == 200
    assert b'data-testid="auth-login-page"' in response.content
    assert b'data-testid="login-form"' in response.content
    assert b"Sign in" in response.content


@pytest.mark.django_db
def test_authenticated_user_redirected_from_login(client, django_user_model):
    """
    Authenticated GET /auth/login/ returns 302 redirect to dashboard.

    :Example:

    force_login → GET /auth/login/ → 302
    """
    user = django_user_model.objects.create_user(username="u", password="p")
    client.force_login(user)
    response = client.get(reverse("auth:login"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_redirect_honours_next_param(client, django_user_model):
    """
    Authenticated GET /auth/login/?next=/graph/ redirects to /graph/.

    :Example:

    force_login → GET /auth/login/?next=/graph/ → 302 Location: /graph/
    """
    user = django_user_model.objects.create_user(username="u2", password="p")
    client.force_login(user)
    response = client.get(reverse("auth:login") + "?next=/graph/")
    assert response.status_code == 302
    assert response["Location"] == "/graph/"


@pytest.mark.django_db
def test_redirect_ignores_external_next_param(client, django_user_model):
    """
    Authenticated GET with external next URL falls back to default redirect.

    Prevents open-redirect attacks where ?next=http://evil.com could redirect
    users to arbitrary external sites.

    :Example:

    force_login → GET /auth/login/?next=http://evil.com → 302 Location: /views/
    """
    user = django_user_model.objects.create_user(username="u3", password="p")
    client.force_login(user)
    response = client.get(reverse("auth:login") + "?next=http://evil.com")
    assert response.status_code == 302
    assert response["Location"] == "/views/"


@pytest.mark.django_db
def test_login_post_success_redirects(client, django_user_model):
    """
    POST valid credentials to /auth/login/ starts a session and redirects.

    Hits the real LoginView — not force_login, not a mockup.

    :Example:

    POST email=elena@example.com password=secret → 302 Location: /views/
    """
    user = django_user_model.objects.create_user(
        username="elena",
        email="elena@example.com",
        password="test-pass-only-1234",
    )
    response = client.post(
        reverse("auth:login"),
        {"email": "elena@example.com", "password": "test-pass-only-1234"},
    )
    assert response.status_code == 302
    assert response["Location"] == "/views/"
    # Session is authenticated
    assert "_auth_user_id" in client.session
    assert int(client.session["_auth_user_id"]) == user.pk


@pytest.mark.django_db
def test_login_post_failure_rerenders_with_error(client, django_user_model):
    """
    POST invalid password re-renders login with an error message.

    :Example:

    POST email=elena@example.com password=wrong → 200, error text present
    """
    django_user_model.objects.create_user(
        username="elena2",
        email="elena2@example.com",
        password="test-pass-only-1234",
    )
    response = client.post(
        reverse("auth:login"),
        {"email": "elena2@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 200
    assert b"Invalid email or password" in response.content
    assert b'data-testid="login-error"' in response.content
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_login_log_story_happy(client, django_user_model, caplog):
    """Successful POST logs credential resolution, session start, and safe next=."""
    django_user_model.objects.create_user(
        username="elena_story",
        email="elena.story@example.com",
        password="test-pass-only-1234",
    )
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.post(
            reverse("auth:login"),
            {"email": "elena.story@example.com", "password": "test-pass-only-1234"},
        )
    assert response.status_code == 302
    assert_log_story(
        caplog,
        where="LoginView.post",
        beats={
            "entry": [" | entry | ", "attempt", "email=elena.story@example.com"],
            "processing": [" | processing | ", "login success", "user_pk="],
            "exit": [" | exit | ", "user_pk="],
        },
    )
    assert_log_story(
        caplog,
        where="LoginView._authenticate_by_email",
        beats={"branch": [" | branch | ", "reason=resolved_email"]},
    )
    assert_log_story(
        caplog,
        where="LoginView._redirect_after_login",
        beats={"branch": [" | branch | ", "reason=next_allowed", "next=/views/"]},
    )
    assert "test-pass-only-1234" not in caplog.text


@pytest.mark.django_db
def test_login_log_story_reject(client, django_user_model, caplog):
    """Failed POST logs why authentication was rejected, never the password."""
    django_user_model.objects.create_user(
        username="elena_fail",
        email="elena.fail@example.com",
        password="test-pass-only-1234",
    )
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.post(
            reverse("auth:login"),
            {"email": "elena.fail@example.com", "password": "wrong-password"},
        )
    assert response.status_code == 200
    assert_log_story(
        caplog,
        where="LoginView.post",
        beats={
            "entry": [" | entry | ", "attempt", "email="],
            "branch": [" | branch | ", "reason=authentication_failed", "email="],
        },
    )
    assert_log_story(
        caplog,
        where="LoginView._authenticate_by_email",
        beats={"branch": [" | branch | ", "reason=resolved_user_auth_failed"]},
    )
    assert "wrong-password" not in caplog.text
    assert "test-pass-only-1234" not in caplog.text


@pytest.mark.django_db
def test_login_get_log_story_already_authenticated(client, django_user_model, caplog):
    """Authenticated GET logs why the form is skipped."""
    user = django_user_model.objects.create_user(username="u_logged_in", password="p")
    client.force_login(user)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.get(reverse("auth:login"))
    assert response.status_code == 302
    assert_log_story(
        caplog,
        where="LoginView.get",
        beats={
            "entry": [" | entry | ", "authenticated=True"],
            "branch": [" | branch | ", "reason=already_authenticated"],
        },
    )


@pytest.mark.django_db
def test_login_get_log_story_unauthenticated(client, caplog):
    """Unauthenticated GET logs why the login form is rendered."""
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.get(reverse("auth:login"))
    assert response.status_code == 200
    assert_log_story(
        caplog,
        where="LoginView.get",
        beats={
            "entry": [" | entry | ", "authenticated=False"],
            "branch": [" | branch | ", "reason=unauthenticated_form"],
            "exit": [" | exit | ", "rendering login form"],
        },
    )


@pytest.mark.django_db
def test_login_redirect_log_story_next_allowed(client, django_user_model, caplog):
    """Relative next= is accepted with an explicit branch reason."""
    user = django_user_model.objects.create_user(username="u_next_ok", password="p")
    client.force_login(user)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.get(reverse("auth:login") + "?next=/graph/")
    assert response.status_code == 302
    assert_log_story(
        caplog,
        where="LoginView._redirect_after_login",
        beats={"branch": [" | branch | ", "reason=next_allowed", "next=/graph/"]},
    )


@pytest.mark.django_db
def test_login_redirect_log_story_open_redirect_rejected(client, django_user_model, caplog):
    """External next= is rejected with an explicit branch reason."""
    user = django_user_model.objects.create_user(username="u_next_bad", password="p")
    client.force_login(user)
    with caplog.at_level(logging.INFO, logger=_AUTH_LOG):
        response = client.get(reverse("auth:login") + "?next=http://evil.com")
    assert response.status_code == 302
    assert_log_story(
        caplog,
        where="LoginView._redirect_after_login",
        beats={
            "branch": [
                " | branch | ",
                "reason=open_redirect_rejected",
                "next=http://evil.com",
                "fallback=/views/",
            ]
        },
    )
