"""
Common AT step helpers and wait steps.

Steps:
  - When the user waits {seconds:d} seconds
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from behave import when

if TYPE_CHECKING:
    from django.test import Client

logger = logging.getLogger(__name__)


def get_client(context) -> Client:
    """Return the Django test client attached by behave-django."""
    return context.test.client


def get_response_content(context) -> str:
    """Decode the last HTTP response body as text."""
    if not hasattr(context, "response"):
        msg = "No HTTP response on context — call a When step that performs a request first."
        raise AssertionError(msg)
    return context.response.content.decode()


@when("the user waits {seconds:d} seconds")
def step_user_waits(context, seconds: int) -> None:
    """Pause execution (AT harness — rarely needed without a browser)."""
    logger.info("Waiting %s seconds", seconds)
    time.sleep(seconds)


# ─── ChangeSet state setup steps (Group B — S33) ────────────────────────────

from behave import given  # noqa: E402


@given("ChangeSet id={cs_id:d} is applied with {count:d} accepted operations")
def step_applied_changeset(context, cs_id, count):
    """Create an applied ChangeSet with N accepted ChangeSetItems in the test DB."""
    raise NotImplementedError()


@given("Marcus clicks [Roll Back Entire Run]")
def step_marcus_clicks_rollback(context):
    """POST to /changesets/<id>/rollback/ via the test client."""
    raise NotImplementedError()


from behave import then, when  # noqa: E402


@when("Marcus clicks [Roll Back Entire Run]")
def step_marcus_clicks_rollback_btn(context):
    """POST to the rollback endpoint for the current ChangeSet in context."""
    raise NotImplementedError()


@then('a new ChangeSet is created with source "rollback"')
def step_rollback_changeset_created(context):
    """Assert a new rollback ChangeSet was created in the DB."""
    raise NotImplementedError()


@then("the rollback ChangeSet reverses all {count:d} operations from ChangeSet id={cs_id:d}")
def step_rollback_reverses_ops(context, count, cs_id):
    """Assert the rollback ChangeSet contains N inverse operations."""
    raise NotImplementedError()
