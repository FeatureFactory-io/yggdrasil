"""
Dialog E2E steps (Playwright, modal interactions).

Steps:
  - When the user confirms the dialog
  - When the user cancels the dialog
  - Then the dialog "{dialog_name}" should be visible
"""

from __future__ import annotations

import logging

from behave import then, when

logger = logging.getLogger(__name__)


def _dialog_test_id(dialog_name: str) -> str:
    return dialog_name if dialog_name.endswith("-dialog") else f"{dialog_name}-dialog"


@when("the user confirms the dialog")
def step_user_confirms_dialog(context) -> None:
    """Click the dialog confirm button."""
    confirm = context.page.get_by_test_id("dialog-confirm-btn")
    if confirm.count() == 0:
        confirm = context.page.get_by_test_id("confirm-dialog-btn")
    confirm.click()
    logger.info("User confirms dialog")


@when("the user cancels the dialog")
def step_user_cancels_dialog(context) -> None:
    """Click the dialog cancel button."""
    cancel = context.page.get_by_test_id("dialog-cancel-btn")
    if cancel.count() == 0:
        cancel = context.page.get_by_test_id("cancel-dialog-btn")
    cancel.click()
    logger.info("User cancels dialog")


@then('the dialog "{dialog_name}" should be visible')
def step_dialog_visible(context, dialog_name: str) -> None:
    """Assert the dialog container is visible."""
    tid = _dialog_test_id(dialog_name)
    assert context.page.get_by_test_id(tid).is_visible(), f"Dialog {dialog_name!r} not visible"
    logger.info("Dialog %s is visible", dialog_name)
