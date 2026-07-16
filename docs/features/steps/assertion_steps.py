"""
Assertion AT steps (Django test client response body).

Steps:
  - Then the user should see "{text}"
  - Then the user should not see "{text}"
  - Then the element "{test_id}" should be visible
"""

from __future__ import annotations

import logging

from behave import then
from steps.common_steps import get_response_content

logger = logging.getLogger(__name__)


@then('the user should see "{text}"')
def step_user_should_see_text(context, text: str) -> None:
    """Assert response body contains ``text``."""
    content = get_response_content(context)
    assert text in content, f'Expected to see "{text}" in response'
    logger.info('User sees "%s"', text)


@then('the user should not see "{text}"')
def step_user_should_not_see_text(context, text: str) -> None:
    """Assert response body does not contain ``text``."""
    content = get_response_content(context)
    assert text not in content, f'Expected not to see "{text}" in response'
    logger.info('User does not see "%s"', text)


@then('the element "{test_id}" should be visible')
def step_element_visible(context, test_id: str) -> None:
    """Assert ``data-testid`` is present in the response HTML."""
    content = get_response_content(context)
    marker = f'data-testid="{test_id}"'
    assert marker in content, f"Element {test_id!r} not found (no {marker} in response)"
    logger.info("Element testid=%s is visible", test_id)
