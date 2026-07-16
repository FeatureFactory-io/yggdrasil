"""
Common E2E step helpers and wait steps (Playwright).

Steps:
  - When the user waits {seconds:d} seconds
"""

from __future__ import annotations

import logging

from behave import when

logger = logging.getLogger(__name__)


def test_id(field: str, suffix: str) -> str:
    """Build a ``data-testid`` following IA naming conventions."""
    if field.endswith(suffix) or field.endswith("-btn") or field.endswith("-input"):
        return field
    return f"{field}{suffix}"


@when("the user waits {seconds:d} seconds")
def step_user_waits(context, seconds: int) -> None:
    """Wait using Playwright's timeout (milliseconds)."""
    context.page.wait_for_timeout(seconds * 1000)
    logger.info("Waited %s seconds", seconds)
