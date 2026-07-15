"""
Assertion E2E steps (Playwright).

Steps:
  - Then the user should see "{text}"
  - Then the user should not see "{text}"
  - Then the element "{test_id}" should be visible
"""

from __future__ import annotations

import logging

from behave import then

logger = logging.getLogger(__name__)


@then('the user should see "{text}"')
def step_user_should_see_text(context, text: str) -> None:
    """Assert visible text appears on the page."""
    locator = context.page.get_by_text(text)
    assert locator.first.is_visible(), f'Expected to see "{text}" on page'
    logger.info('User sees "%s"', text)


@then('the user should not see "{text}"')
def step_user_should_not_see_text(context, text: str) -> None:
    """Assert text is not visible on the page."""
    locator = context.page.get_by_text(text)
    assert (
        locator.count() == 0 or not locator.first.is_visible()
    ), f'Expected not to see "{text}" on page'
    logger.info('User does not see "%s"', text)


@then('the element "{test_id}" should be visible')
def step_element_visible(context, test_id: str) -> None:
    """Assert element with ``data-testid`` is visible."""
    assert context.page.get_by_test_id(
        test_id
    ).is_visible(), f"Element testid={test_id} is not visible"
    logger.info("Element testid=%s is visible", test_id)
