"""
Integration tests for TokenListView (GET /auth/tokens/).

Tests use the Django test client against the real view — no mocks.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from yggdrasil.auth.models import PersonalAccessToken


@pytest.mark.django_db
def test_token_list_requires_login(client):
    """
    Unauthenticated GET /auth/tokens/ redirects to login.

    :Example:

    GET /auth/tokens/ (anon) → 302 → /auth/login/?next=/auth/tokens/
    """
    response = client.get(reverse("auth:token_list"))
    assert response.status_code == 302
    assert "/auth/login/" in response["Location"]


@pytest.mark.django_db
def test_token_list_shows_users_tokens(client, django_user_model):
    """
    Authenticated GET /auth/tokens/ renders only the logged-in user's tokens.

    Verifies name and scope columns appear in the response; token_hash must
    never appear (security: hash is not a template variable).

    :Example:

    force_login → GET /auth/tokens/ → 200, body contains "laptop-ratatosk"
    """
    secret_hash_a = "aabbccddeeff00112233445566778899aabbccddeeff00112233445566778899"
    secret_hash_b = "ffeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100"
    user = django_user_model.objects.create_user(username="priya", password="p")
    PersonalAccessToken.objects.create(
        user=user, name="laptop-ratatosk", token_hash=secret_hash_a, scope="read-write"
    )
    PersonalAccessToken.objects.create(
        user=user, name="cursor-mcp", token_hash=secret_hash_b, scope="read-only"
    )
    client.force_login(user)

    response = client.get(reverse("auth:token_list"))

    assert response.status_code == 200
    assert b"laptop-ratatosk" in response.content
    assert b"cursor-mcp" in response.content
    assert b"read-write" in response.content
    assert b"read-only" in response.content
    # token_hash must never reach the template context
    assert secret_hash_a.encode() not in response.content
    assert secret_hash_b.encode() not in response.content


@pytest.mark.django_db
def test_token_list_does_not_leak_other_users_tokens(client, django_user_model):
    """
    Tokens belonging to other users are never included in the response.

    Verifies strict owner filtering in TokenService.list_tokens.

    :Example:

    user_a has token "secret-a"; user_b logs in → "secret-a" not in response
    """
    user_a = django_user_model.objects.create_user(username="ua", password="p")
    user_b = django_user_model.objects.create_user(username="ub", password="p")
    PersonalAccessToken.objects.create(
        user=user_a, name="secret-a", token_hash="ha", scope="read-only"
    )
    client.force_login(user_b)

    response = client.get(reverse("auth:token_list"))

    assert response.status_code == 200
    assert b"secret-a" not in response.content


@pytest.mark.django_db
def test_token_page_shows_usage_snippets(client, django_user_model):
    """
    Authenticated GET /auth/tokens/ includes CLI usage snippets for Ratatosk and MCP.

    Verifies that the page contains the install command and the token env-var
    name so users can copy-paste without consulting external docs.

    :Example:

    force_login → GET /auth/tokens/ → 200, "pip install ratatosk" in body
    """
    user = django_user_model.objects.create_user(username="snippet_user", password="p")
    client.force_login(user)

    response = client.get(reverse("auth:token_list"))

    assert response.status_code == 200
    assert b"pip install ratatosk" in response.content
    assert b"YGGDRASIL_TOKEN" in response.content


@pytest.mark.django_db
def test_token_list_empty_state(client, django_user_model):
    """
    Authenticated GET with no tokens renders the empty-state row.

    :Example:

    force_login (no tokens) → 200, body contains "No tokens yet."
    """
    user = django_user_model.objects.create_user(username="empty", password="p")
    client.force_login(user)

    response = client.get(reverse("auth:token_list"))

    assert response.status_code == 200
    assert b"No tokens yet." in response.content


@pytest.mark.django_db
def test_token_page_shows_nav_settings_and_user_menu(client, django_user_model):
    """
    Authenticated GET /auth/tokens/ includes nav-settings and user-menu testids.

    Both testids must be present so the navigation links to the settings page
    and the user dropdown is accessible from the token management screen.

    :Example:

    force_login → GET /auth/tokens/ → 200, data-testid="nav-settings" present
    """
    user = django_user_model.objects.create_user(username="nav_user", password="p")
    client.force_login(user)

    response = client.get(reverse("auth:token_list"))

    assert response.status_code == 200
    assert b'data-testid="nav-settings"' in response.content
    assert b'data-testid="user-menu"' in response.content


@pytest.mark.django_db
def test_login_page_has_no_navbar(client):
    """
    GET /auth/login/ does not include nav-settings or user-menu testids.

    The login page is a standalone page with no active session, so the
    navbar must be absent to avoid UI confusion.

    :Example:

    GET /auth/login/ → 200, no data-testid="nav-settings" in body
    """
    response = client.get(reverse("auth:login"))

    assert response.status_code == 200
    assert b'data-testid="nav-settings"' not in response.content
    assert b'data-testid="user-menu"' not in response.content
