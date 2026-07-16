"""
Navigation AT steps (Django test client).

Steps:
  - Given the user is on the "{page_name}" page
  - When the user navigates to the "{page_name}" page
  - Then the user should see the "{page_name}" page
"""

from __future__ import annotations

import logging

from behave import given, then, when
from steps.common_steps import get_client
from support.pages import resolve_page_path

logger = logging.getLogger(__name__)


@given('the user is on the "{page_name}" page')
def step_user_is_on_page(context, page_name: str) -> None:
    """GET the registered page and store the response on context."""
    path = resolve_page_path(page_name)
    context.response = get_client(context).get(path)
    context.current_page = page_name
    logger.info("User on page %s (%s) -> %s", page_name, path, context.response.status_code)


@when('the user navigates to the "{page_name}" page')
def step_user_navigates_to_page(context, page_name: str) -> None:
    """Navigate to the registered page (alias of Given for When phrasing)."""
    step_user_is_on_page(context, page_name)


@then('the user should see the "{page_name}" page')
def step_user_should_see_page(context, page_name: str) -> None:
    """Assert the last response is HTTP 200 for the expected page."""
    assert (
        context.response.status_code == 200
    ), f"Expected page {page_name} to return 200, got {context.response.status_code}"
    logger.info("User sees page %s", page_name)
