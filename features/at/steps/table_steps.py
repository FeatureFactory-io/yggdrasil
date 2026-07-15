"""
Table AT steps (Django test client, HTML substring checks).

Steps:
  - Then the user sees table "{table_name}" with {n:d} rows
  - Then the table "{table_name}" should contain "{text}"
  - When the user sorts table "{table_name}" by "{column}"
"""

from __future__ import annotations

import logging
import re

from behave import then, when
from features.at.steps.common_steps import get_response_content

logger = logging.getLogger(__name__)


def _table_test_id(table_name: str) -> str:
    return table_name if table_name.endswith("-table") else f"{table_name}-table"


def _table_html(context, table_name: str) -> str:
    content = get_response_content(context)
    test_id = _table_test_id(table_name)
    assert f'data-testid="{test_id}"' in content, f"Table testid={test_id} not found"
    match = re.search(
        rf'<table[^>]*data-testid="{re.escape(test_id)}"[^>]*>.*?</table>',
        content,
        re.DOTALL | re.IGNORECASE,
    )
    assert match, f"Could not extract table HTML for testid={test_id}"
    return match.group(0)


@then('the user sees table "{table_name}" with {n:d} rows')
def step_user_sees_table_rows(context, table_name: str, n: int) -> None:
    """Count ``<tr>`` elements with ``data-testid`` ending in ``-row`` inside the table."""
    html = _table_html(context, table_name)
    rows = re.findall(r'data-testid="[^"]*-row"', html)
    assert len(rows) == n, f"Expected {n} rows in {table_name}, found {len(rows)}"
    logger.info("Table %s has %s rows", table_name, n)


@then('the table "{table_name}" should contain "{text}"')
def step_table_contains_text(context, table_name: str, text: str) -> None:
    """Assert table body contains ``text``."""
    html = _table_html(context, table_name)
    assert text in html, f'Table {table_name} does not contain "{text}"'
    logger.info('Table %s contains "%s"', table_name, text)


@when('the user sorts table "{table_name}" by "{column}"')
def step_user_sorts_table(context, table_name: str, column: str) -> None:
    """Click sort control for ``column`` (AT: verify sort header exists)."""
    html = _table_html(context, table_name)
    sort_test_id = f"sort-{column}-btn"
    assert (
        f'data-testid="{sort_test_id}"' in html
    ), f"Sort control testid={sort_test_id} not found in table {table_name}"
    logger.info("User sorts table %s by %s (AT: presence check only)", table_name, column)
