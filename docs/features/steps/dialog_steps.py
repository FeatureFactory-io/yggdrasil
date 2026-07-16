"""
Dialog AT steps (Django test client, modal presence checks).

Steps:
  - When the user confirms the dialog
  - When the user cancels the dialog
  - Then the dialog "{dialog_name}" should be visible
"""

from __future__ import annotations

import logging

from behave import then, when
from steps.common_steps import get_response_content

logger = logging.getLogger(__name__)


def _dialog_test_id(dialog_name: str) -> str:
    return dialog_name if dialog_name.endswith("-dialog") else f"{dialog_name}-dialog"


@when("the user confirms the dialog")
def step_user_confirms_dialog(context) -> None:
    """Verify confirm control exists (AT: no real modal interaction)."""
    content = get_response_content(context)
    assert (
        'data-testid="dialog-confirm-btn"' in content
        or 'data-testid="confirm-dialog-btn"' in content
    )
    logger.info("User confirms dialog (AT: presence check only)")


@when("the user cancels the dialog")
def step_user_cancels_dialog(context) -> None:
    """Verify cancel control exists (AT: no real modal interaction)."""
    content = get_response_content(context)
    assert (
        'data-testid="dialog-cancel-btn"' in content or 'data-testid="cancel-dialog-btn"' in content
    )
    logger.info("User cancels dialog (AT: presence check only)")


@then('the dialog "{dialog_name}" should be visible')
def step_dialog_visible(context, dialog_name: str) -> None:
    """Assert dialog container ``data-testid`` is in the response."""
    content = get_response_content(context)
    test_id = _dialog_test_id(dialog_name)
    marker = f'data-testid="{test_id}"'
    assert marker in content, f"Dialog {dialog_name!r} not visible (no {marker})"
    logger.info("Dialog %s is visible", dialog_name)
