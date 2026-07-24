"""Integration tests for the marketing landing page (web:index)."""

from __future__ import annotations

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_anonymous_landing_shows_navbar_login(client):
    """Anonymous GET / shows marketing landing with top-right Sign In."""
    response = client.get(reverse("web:index"))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="landing-loaded"' in body
    assert 'data-testid="landing-hero"' in body
    assert 'data-testid="navbar-login"' in body
    assert 'href="/auth/login/"' in body


@pytest.mark.django_db
def test_anonymous_landing_cta_points_to_login(client):
    """Hero Get Started links to the real login page, not Django admin."""
    response = client.get(reverse("web:index"))
    body = response.content.decode()
    assert 'data-testid="landing-cta-signin"' in body
    assert "/admin/" not in body
    assert 'href="/auth/login/"' in body


@pytest.mark.django_db
def test_authenticated_root_redirects_to_view_browser(client, django_user_model):
    """Authenticated GET / skips marketing landing and opens View Browser."""
    user = django_user_model.objects.create_user(username="architect", password="secret")
    client.force_login(user)
    response = client.get(reverse("web:index"))
    assert response.status_code == 302
    assert response["Location"] == reverse("web:view_browse")


@pytest.mark.django_db
def test_view_browser_requires_login(client):
    """Unauthenticated GET /views/ redirects to login."""
    response = client.get(reverse("web:view_browse"))
    assert response.status_code == 302
    assert "/auth/login/" in response["Location"]


@pytest.mark.django_db
def test_view_browser_renders_for_authenticated_user(client, django_user_model):
    """Authenticated GET /views/ renders VIEW-BROWSE-1 shell."""
    user = django_user_model.objects.create_user(username="architect", password="secret")
    client.force_login(user)
    response = client.get(reverse("web:view_browse"))
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="view-browse-page"' in body
    assert 'data-testid="filters-toggle"' in body
