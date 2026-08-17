"""
Assertion AT steps (Django test client response body).

Steps:
  - Then the user should see "{text}"
  - Then the user should not see "{text}"
  - Then the element "{test_id}" should be visible
  - Then the element "{test_id}" should not be visible
  - Then the page uses the full-height view browser layout
  - Then the response is an embed partial
"""

from __future__ import annotations

import logging
import re

from behave import then
from steps.common_steps import get_response_content
from support.visibility import assert_testid_hidden, assert_testid_visible

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
    """Assert ``data-testid`` is present and not SSR-hidden (``d-none`` / table mode)."""
    content = get_response_content(context)
    assert_testid_visible(content, test_id)
    logger.info("Element testid=%s is visible", test_id)


@then('the element "{test_id}" should not be visible')
def step_element_not_visible(context, test_id: str) -> None:
    """Assert ``data-testid`` is absent or SSR-hidden."""
    content = get_response_content(context)
    assert_testid_hidden(content, test_id)
    logger.info("Element testid=%s is not visible", test_id)


@then('the element "{test_id}" is disabled')
def step_element_is_disabled(context, test_id: str) -> None:
    """Assert ``data-testid`` element has a ``disabled`` attribute."""
    content = get_response_content(context)
    pattern = rf'data-testid="{re.escape(test_id)}"[^>]*disabled'
    assert re.search(pattern, content), f"Expected testid={test_id!r} to be disabled"
    logger.info("Element testid=%s is disabled", test_id)


@then('the element "{test_id}" shows "{text}"')
def step_element_shows_text(context, test_id: str, text: str) -> None:
    """Assert element with ``data-testid`` contains ``text``."""
    content = get_response_content(context)
    tag_pattern = rf'<[^>]*data-testid="{re.escape(test_id)}"[^>]*>.*?</[^>]+>'
    match = re.search(tag_pattern, content, re.DOTALL)
    assert match, f"Element testid={test_id!r} not found"
    assert text in match.group(0), f"Expected {text!r} in element {test_id!r}"
    logger.info("Element testid=%s shows %s", test_id, text)


@then("the page uses the full-height view browser layout")
def step_page_uses_view_browser_layout(context) -> None:
    """Assert ``yrg-view-browser`` appears on the ``<body>`` class list."""
    content = get_response_content(context)
    assert re.search(
        r'<body[^>]*class="[^"]*\byrg-view-browser\b', content
    ), "Expected yrg-view-browser on <body class=...>"
    logger.info("Page uses full-height view browser layout")


@then("the response is an embed partial")
def step_response_is_embed_partial(context) -> None:
    """Assert response is a minimal embed partial (no full chrome)."""
    content = get_response_content(context)
    assert "nav-view-browser" not in content, "Embed partial must not include nav-view-browser"
    assert (
        'data-testid="browser-nav-panel"' not in content
    ), "Embed partial must not include navigator"
    logger.info("Response is an embed partial")
