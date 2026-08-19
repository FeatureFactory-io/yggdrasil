"""Request execution ray: views, services, and helpers share one trace."""

from __future__ import annotations

import logging

import pytest
from django.test import Client, override_settings
from django.urls import reverse
from tests.support.log_story import assert_log_story

from yggdrasil.request_trace import traced_request
from yggdrasil.web.browse_helpers import build_package_tree


@pytest.fixture()
def client() -> Client:
    return Client()


def _trace_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    """Return RequestTrace log messages in capture order."""
    return [
        record.getMessage() for record in caplog.records if "RequestTrace |" in record.getMessage()
    ]


def _entry_wheres(messages: list[str]) -> list[str]:
    """Extract ``where=`` values from RequestTrace entry lines."""
    wheres: list[str] = []
    for message in messages:
        if "RequestTrace | entry |" not in message:
            continue
        marker = "where="
        start = message.find(marker)
        if start == -1:
            continue
        wheres.append(message[start + len(marker) :].split()[0])
    return wheres


@override_settings(REQUEST_TRACE=False)
@pytest.mark.django_db
def test_request_trace_disabled_emits_no_ray(
    client: Client, caplog: pytest.LogCaptureFixture
) -> None:
    """REQUEST_TRACE=False must not emit RequestTrace lines."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    client.get("/health/")
    assert _trace_messages(caplog) == []


@override_settings(REQUEST_TRACE=True)
@pytest.mark.django_db
def test_health_trace_includes_controller(client: Client, caplog: pytest.LogCaptureFixture) -> None:
    """Health request ray includes the view function."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    client.get("/health/")
    wheres = _entry_wheres(_trace_messages(caplog))
    assert any(where.endswith("health") for where in wheres)


@override_settings(REQUEST_TRACE=True)
@pytest.mark.django_db
def test_browse_trace_spans_controller_and_service(
    client: Client,
    view_browser_user,
    view_browser_explorer_model,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One browse request traces web views and graph browse_service."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    client.force_login(view_browser_user)
    client.get(reverse("web:view_browse_model", kwargs={"model_slug": "yggdrasil"}))
    wheres = _entry_wheres(_trace_messages(caplog))
    assert any("ViewBrowseView.get" in where for where in wheres)
    assert any("browse_service.user_can_read_model" in where for where in wheres)
    assert any("build_view_browse_context" in where for where in wheres)
    assert view_browser_explorer_model.slug == "yggdrasil"


@override_settings(REQUEST_TRACE=True)
@pytest.mark.django_db
def test_browse_trace_shares_request_id(
    client: Client,
    view_browser_user,
    view_browser_explorer_model,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Every RequestTrace record carries the response request_id."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    client.force_login(view_browser_user)
    response = client.get(reverse("web:view_browse_model", kwargs={"model_slug": "yggdrasil"}))
    request_id = response["X-Request-Id"]
    records = [record for record in caplog.records if "RequestTrace |" in record.getMessage()]
    assert records
    assert {record.request_id for record in records} == {request_id}
    assert view_browser_explorer_model.slug == "yggdrasil"


@override_settings(REQUEST_TRACE=True)
def test_trace_nests_helper_under_caller(caplog: pytest.LogCaptureFixture) -> None:
    """Nested yggdrasil calls increase depth on the ray."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    elements = [
        {"name": "API", "package": "Application", "package_slug": "application"},
    ]
    with traced_request(enabled=True):
        build_package_tree(elements)
    entries = [
        record.getMessage()
        for record in caplog.records
        if "RequestTrace | entry |" in record.getMessage()
    ]
    tree_line = next(line for line in entries if "build_package_tree" in line)
    child_line = next(line for line in entries if "_package_key" in line)
    tree_depth = int(tree_line.split("depth=")[1].split()[0])
    child_depth = int(child_line.split("depth=")[1].split()[0])
    assert child_depth == tree_depth + 1


@override_settings(REQUEST_TRACE=True)
@pytest.mark.django_db
def test_request_trace_log_story_happy(client: Client, caplog: pytest.LogCaptureFixture) -> None:
    """Health ray logs entry and exit beats for the view."""
    caplog.set_level(logging.INFO, logger="yggdrasil.trace")
    client.get("/health/")
    assert_log_story(
        caplog,
        where="RequestTrace",
        beats={
            "entry": ["entry", "depth=", "where=", "health"],
            "exit": ["exit", "depth=", "where=", "health", "duration_ms="],
        },
    )
