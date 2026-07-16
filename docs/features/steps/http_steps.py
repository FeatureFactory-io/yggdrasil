"""
HTTP-level AT steps (Django test client, no browser).

Steps:
  - Given the application is running
  - When I GET "{path}"
  - Then the response status is {status:d}
  - Then the response body contains "{key}": "{value}"
"""

from __future__ import annotations

import json
import logging

from behave import given, then, when
from steps.common_steps import get_client

logger = logging.getLogger(__name__)


@given("the application is running")
def step_application_is_running(context) -> None:
    """Assert the Django test harness is ready (no external process required)."""
    client = get_client(context)
    response = client.get("/health/")
    logger.info("Application reachable: GET /health/ -> %s", response.status_code)
    assert response.status_code == 200


@when('I GET "{path}"')
def step_get_path(context, path: str) -> None:
    """Perform an HTTP GET against ``path`` via the Django test client."""
    context.response = get_client(context).get(path)
    logger.info("GET %s -> %s", path, context.response.status_code)


@then("the response status is {status:d}")
def step_response_status(context, status: int) -> None:
    """Assert the last response HTTP status code."""
    assert (
        context.response.status_code == status
    ), f"Expected status {status}, got {context.response.status_code}"
    logger.info("Response status is %s", status)


@then('the response body contains "{key}": "{value}"')
def step_response_body_contains_key_value(context, key: str, value: str) -> None:
    """Assert JSON response body contains ``key`` with string ``value``."""
    body = json.loads(context.response.content)
    actual = body.get(key)
    assert actual == value, f"Expected {key}={value!r}, got {actual!r}"
    logger.info('Response body contains "%s": "%s"', key, value)
