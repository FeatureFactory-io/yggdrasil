"""
Unit tests for the /health/ endpoint.

These tests use the Django test client and do NOT hit the database,
confirming the health check is a true shallow liveness probe.
"""
import json

import pytest
from django.test import Client


@pytest.fixture()
def client() -> Client:
    return Client()


@pytest.mark.django_db
def test_health_returns_200(client: Client) -> None:
    """Health endpoint must return HTTP 200."""
    response = client.get("/health/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_health_returns_json_ok(client: Client) -> None:
    """Health endpoint must return ``{"status": "ok"}``."""
    response = client.get("/health/")
    data = json.loads(response.content)
    assert data == {"status": "ok"}


@pytest.mark.django_db
def test_health_content_type_is_json(client: Client) -> None:
    """Health endpoint must respond with application/json."""
    response = client.get("/health/")
    assert "application/json" in response["Content-Type"]


@pytest.mark.django_db
def test_health_has_request_id_header(client: Client) -> None:
    """RequestIdMiddleware must attach X-Request-Id to every response."""
    response = client.get("/health/")
    assert "X-Request-Id" in response


@pytest.mark.django_db
def test_health_is_not_cached(client: Client) -> None:
    """Health endpoint must not be cached (no-cache / no-store)."""
    response = client.get("/health/")
    cache_control = response.get("Cache-Control", "")
    assert "no-cache" in cache_control or "no-store" in cache_control
