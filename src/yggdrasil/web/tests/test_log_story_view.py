"""Request-id log story viewer tests."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client, override_settings

from yggdrasil.web.log_story import load_recent_requests, load_request_story


@pytest.fixture()
def client() -> Client:
    return Client()


@override_settings(DEBUG=False)
@pytest.mark.django_db
def test_log_story_hidden_when_debug_off(client: Client) -> None:
    """Log story page is a local debug tool, not a production screen."""
    response = client.get("/__logs/")
    assert response.status_code == 404


@override_settings(DEBUG=True)
@pytest.mark.django_db
def test_log_story_page_renders(client: Client) -> None:
    """DEBUG log story page returns the viewer chrome."""
    response = client.get("/__logs/")
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="log-story-page"' in body
    assert "Request story" in body


@override_settings(DEBUG=True, REQUEST_TRACE=True)
@pytest.mark.django_db
def test_log_story_shows_health_request(client: Client) -> None:
    """A health request can be read back as a story keyed by request_id."""
    request_id = "story-health-ray-001"
    health = client.get("/health/", HTTP_X_REQUEST_ID=request_id)
    assert health["X-Request-Id"] == request_id
    _flush_app_log()
    response = client.get("/__logs/", {"request_id": request_id})
    body = response.content.decode()
    assert response.status_code == 200
    assert request_id in body
    assert "request started" in body
    assert 'data-testid="log-story-entry"' in body


@override_settings(DEBUG=True)
def test_log_story_loader_parses_json_lines(tmp_path: Path) -> None:
    """Loader groups JSON lines by request_id and keeps context blocks."""
    log_path = tmp_path / "app.log"
    log_path.write_text(
        json.dumps(
            {
                "event": "Room entrance detected",
                "level": "info",
                "logger": "yggdrasil.web",
                "timestamp": "2026-08-19T14:13:01.234000Z",
                "request_id": "req-hp",
                "path": "/chamber/",
                "module": "yggdrasil.web.views",
                "thread": "actor-hp-001",
                "line": 42,
                "context": {"room_id": "chamber_of_secrets"},
            }
        )
        + "\n"
        + json.dumps(
            {
                "event": "Enemy detected in chamber",
                "level": "warning",
                "logger": "yggdrasil.graph",
                "timestamp": "2026-08-19T14:13:02.234000Z",
                "request_id": "req-hp",
                "path": "/chamber/",
                "module": "yggdrasil.graph.browse",
                "thread": "actor-vol-001",
                "line": 88,
                "context": {"threat": "CRITICAL"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    requests = load_recent_requests(log_path)
    assert requests[0]["request_id"] == "req-hp"
    assert requests[0]["entry_count"] == 2
    story = load_request_story(log_path, "req-hp")
    assert story is not None
    assert story["entries"][0]["event"] == "Room entrance detected"
    assert story["entries"][0]["context"]["room_id"] == "chamber_of_secrets"
    assert story["entries"][1]["level"] == "warning"


def _flush_app_log() -> None:
    """Flush rotating handlers so the viewer can read lines just written."""
    log_path = Path(settings.LOGS_DIR) / "app.log"
    for handler in logging.getLogger("yggdrasil.web").handlers:
        handler.flush()
    for handler in logging.getLogger("yggdrasil").handlers:
        handler.flush()
    assert log_path.exists()
