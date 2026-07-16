"""
Table E2E steps (Playwright, data-testid selectors).

Steps:
  - Then the user sees table "{table_name}" with {n:d} rows
  - Then the table "{table_name}" should contain "{text}"
  - When the user sorts table "{table_name}" by "{column}"
"""

from __future__ import annotations

import logging

from behave import then, when
from step_helpers import test_id

logger = logging.getLogger(__name__)


def _table_locator(context, table_name: str):
    tid = test_id(table_name, "-table")
    return context.page.get_by_test_id(tid)


@then('the user sees table "{table_name}" with {n:d} rows')
def step_user_sees_table_rows(context, table_name: str, n: int) -> None:
    """Count row elements inside the table."""
    table = _table_locator(context, table_name)
    rows = table.locator('[data-testid$="-row"]')
    assert rows.count() == n, f"Expected {n} rows, found {rows.count()}"
    logger.info("Table %s has %s rows", table_name, n)


@then('the table "{table_name}" should contain "{text}"')
def step_table_contains_text(context, table_name: str, text: str) -> None:
    """Assert table body contains visible text."""
    table = _table_locator(context, table_name)
    assert table.get_by_text(text).count() > 0, f'Table {table_name} does not contain "{text}"'
    logger.info('Table %s contains "%s"', table_name, text)


@when('the user sorts table "{table_name}" by "{column}"')
def step_user_sorts_table(context, table_name: str, column: str) -> None:
    """Click the sort control for ``column``."""
    sort_tid = f"sort-{column}-btn"
    _table_locator(context, table_name).get_by_test_id(sort_tid).click()
    logger.info("User sorts table %s by %s", table_name, column)
