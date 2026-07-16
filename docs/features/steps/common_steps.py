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
