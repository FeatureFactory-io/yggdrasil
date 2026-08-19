"""Request-id correlation: every log line in a request shares one request_id."""

from __future__ import annotations

import logging

import pytest
from django.test import Client
from django.urls import reverse
from tests.support.log_story import assert_log_story


@pytest.fixture()
def client() -> Client:
    return Client()


def _yggdrasil_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """Return captured records from Yggdrasil loggers."""
    return [record for record in caplog.records if record.name.startswith("yggdrasil")]


def _record_request_ids(records: list[logging.LogRecord]) -> set[str]:
    """Collect request_id attributes from log records."""
    return {record.request_id for record in records if hasattr(record, "request_id")}


@pytest.mark.django_db
def test_health_echoes_inbound_request_id(client: Client) -> None:
    """Inbound X-Request-Id is reused on the response."""
    response = client.get("/health/", HTTP_X_REQUEST_ID="req-inbound-42")
    assert response["X-Request-Id"] == "req-inbound-42"


@pytest.mark.django_db
def test_request_id_log_story_happy(client: Client, caplog: pytest.LogCaptureFixture) -> None:
    """Middleware logs entry/exit beats with method, path, and status."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    client.get("/health/")
    assert_log_story(
        caplog,
        where="RequestIdMiddleware",
        beats={
            "entry": ["entry", "request started", "method=GET", "path=/health/"],
            "exit": ["exit", "request completed", "status_code=200", "duration_ms="],
        },
    )


@pytest.mark.django_db
def test_health_logs_share_response_request_id(
    client: Client, caplog: pytest.LogCaptureFixture
) -> None:
    """Every yggdrasil.web log record for a request carries the response request_id."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    response = client.get("/health/")
    request_id = response["X-Request-Id"]
    records = [record for record in _yggdrasil_records(caplog) if record.name == "yggdrasil.web"]
    assert records
    assert _record_request_ids(records) == {request_id}


@pytest.mark.django_db
def test_distinct_requests_get_distinct_request_ids(client: Client) -> None:
    """Two sequential requests must not reuse the same request_id."""
    first = client.get("/health/")["X-Request-Id"]
    second = client.get("/health/")["X-Request-Id"]
    assert first != second


@pytest.mark.django_db
def test_request_id_correlates_web_and_graph_logs(
    client: Client,
    view_browser_user,
    view_browser_explorer_model,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Web and graph loggers on one browse request share the response request_id."""
    caplog.set_level(logging.INFO, logger="yggdrasil.web")
    caplog.set_level(logging.INFO, logger="yggdrasil.graph.browse")
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse_model", kwargs={"model_slug": "yggdrasil"}))
    request_id = response["X-Request-Id"]

    web_records = [record for record in caplog.records if record.name.startswith("yggdrasil.web")]
    graph_records = [
        record for record in caplog.records if record.name.startswith("yggdrasil.graph")
    ]
    assert web_records
    assert graph_records
    assert _record_request_ids(web_records) == {request_id}
    assert _record_request_ids(graph_records) == {request_id}
    assert view_browser_explorer_model.slug == "yggdrasil"
