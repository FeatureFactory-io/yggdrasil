"""
Form E2E steps (Playwright, data-testid selectors).

Steps:
  - When the user enters "{value}" into "{field}"
  - When the user selects "{option}" from "{dropdown}"
  - When the user clicks "{button}"
  - When the user submits the form
"""

from __future__ import annotations

import logging

from behave import when
from features.e2e.steps.common_steps import test_id

logger = logging.getLogger(__name__)


@when('the user enters "{value}" into "{field}"')
def step_user_enters_value(context, value: str, field: str) -> None:
    """Fill an input identified by ``data-testid``."""
    tid = test_id(field, "-input")
    context.page.get_by_test_id(tid).fill(value)
    logger.info('User enters "%s" into testid=%s', value, tid)


@when('the user selects "{option}" from "{dropdown}"')
def step_user_selects_option(context, option: str, dropdown: str) -> None:
    """Select an option from a ``<select>`` by ``data-testid``."""
    tid = test_id(dropdown, "-select")
    context.page.get_by_test_id(tid).select_option(option)
    logger.info('User selects "%s" from testid=%s', option, tid)


@when('the user clicks "{button}"')
def step_user_clicks_button(context, button: str) -> None:
    """Click a control by ``data-testid``."""
    tid = test_id(button, "-btn")
    context.page.get_by_test_id(tid).click()
    logger.info("User clicks testid=%s", tid)


@when("the user submits the form")
def step_user_submits_form(context) -> None:
    """Submit the nearest form (click submit button or press Enter)."""
    submit = context.page.locator('[type="submit"]').first
    if submit.count() > 0:
        submit.click()
    else:
        context.page.keyboard.press("Enter")
    logger.info("User submitted form")
