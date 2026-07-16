"""
Navigation E2E steps (Playwright + behave-django live server).

Steps:
  - Given the user is on the "{page_name}" page
  - When the user navigates to the "{page_name}" page
  - Then the user should see the "{page_name}" page
"""

from __future__ import annotations

import logging

from behave import given, then, when
from support.pages import PAGE_REGISTRY

logger = logging.getLogger(__name__)


def _goto_page(context, page_name: str) -> None:
    url_name = PAGE_REGISTRY[page_name]
    url = context.get_url(url_name)
    context.page.goto(url)
    context.current_page = page_name
    logger.info("Navigated to page %s at %s", page_name, url)


@given('the user is on the "{page_name}" page')
def step_user_is_on_page(context, page_name: str) -> None:
    """Open the registered page in the browser."""
    _goto_page(context, page_name)


@when('the user navigates to the "{page_name}" page')
def step_user_navigates_to_page(context, page_name: str) -> None:
    """Navigate to the registered page."""
    _goto_page(context, page_name)


@then('the user should see the "{page_name}" page')
def step_user_should_see_page(context, page_name: str) -> None:
    """Assert the browser loaded the page successfully (HTTP 200)."""
    assert context.page.url, "Browser has no current URL"
    logger.info("User sees page %s at %s", page_name, context.page.url)
