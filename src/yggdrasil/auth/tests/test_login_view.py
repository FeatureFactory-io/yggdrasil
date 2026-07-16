"""
Integration tests for LoginView (GET /auth/login/).

Tests use the Django test client against the real view — no mocks.
"""

from __future__ import annotations

import pytest
from django.urls import reverse


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

    force_login → GET /auth/login/?next=http://evil.com → 302 Location: /
    """
    user = django_user_model.objects.create_user(username="u3", password="p")
    client.force_login(user)
    response = client.get(reverse("auth:login") + "?next=http://evil.com")
    assert response.status_code == 302
    assert response["Location"] == "/"
