"""
View Browser E2E steps (Playwright).

Steps:
  - Given Priya is on the View Browser
"""

from __future__ import annotations

import logging

from behave import given

logger = logging.getLogger(__name__)


@given("Priya is on the View Browser")
def step_priya_on_view_browser_e2e(context) -> None:
    """Open production View Browser in Playwright."""
    url = context.get_url("web:view_browse")
    context.page.goto(url)
    logger.info("Priya opened View Browser at %s", url)


@given("Priya is on the View Browser with the navigator expanded")
def step_priya_view_browser_nav_expanded_e2e(context) -> None:
    """Open View Browser — navigator SSR expanded for Application package."""
    step_priya_on_view_browser_e2e(context)
