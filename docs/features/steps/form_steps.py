"""
Form AT steps (Django test client, data-testid selectors).

Steps:
  - When the user enters "{value}" into "{field}"
  - When the user selects "{option}" from "{dropdown}"
  - When the user clicks "{button}"
  - When the user submits the form
"""

from __future__ import annotations

import logging

from behave import when
from steps.common_steps import get_client

logger = logging.getLogger(__name__)


def _ensure_form_data(context) -> dict[str, str]:
    if not hasattr(context, "form_data"):
        context.form_data = {}
    return context.form_data


def _field_test_id(field: str) -> str:
    """Return the ``data-testid`` for a form field (IA convention: ``{field}-input``)."""
    if field.endswith("-input") or field.endswith("-select"):
        return field
    return f"{field}-input"


@when('the user enters "{value}" into "{field}"')
def step_user_enters_value(context, value: str, field: str) -> None:
    """Record a form field value for the next submit (by ``data-testid`` name)."""
    form_data = _ensure_form_data(context)
    test_id = _field_test_id(field)
    form_data[test_id] = value
    logger.info('User enters "%s" into field testid=%s', value, test_id)


@when('the user selects "{option}" from "{dropdown}"')
def step_user_selects_option(context, option: str, dropdown: str) -> None:
    """Record a dropdown selection for the next submit."""
    form_data = _ensure_form_data(context)
    test_id = f"{dropdown}-select" if not dropdown.endswith("-select") else dropdown
    form_data[test_id] = option
    logger.info('User selects "%s" from dropdown testid=%s', option, test_id)


@when('the user clicks "{button}"')
def step_user_clicks_button(context, button: str) -> None:
    """Simulate clicking a control identified by ``data-testid``."""
    test_id = button if button.endswith("-btn") else f"{button}-btn"
    content = context.response.content.decode()
    assert f'data-testid="{test_id}"' in content, f"Button testid={test_id} not found in page"
    logger.info("User clicks button testid=%s (AT: presence check only)", test_id)


@when("the user submits the form")
def step_user_submits_form(context) -> None:
    """POST accumulated form data to the current page URL."""
    form_data = _ensure_form_data(context)
    path = context.response.request["PATH_INFO"]
    context.response = get_client(context).post(path, data=form_data)
    logger.info("User submitted form to %s -> %s", path, context.response.status_code)
    context.form_data = {}
