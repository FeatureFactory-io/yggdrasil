"""
Auth E2E steps — stubs until login UI ships (BPE).

Steps:
  - Given the user is logged in as "{role}"  (NotImplementedError)
  - Given the user is not authenticated
"""

from __future__ import annotations

import logging

from behave import given

logger = logging.getLogger(__name__)


@given('the user is logged in as "{role}"')
def step_user_logged_in_as(context, role: str) -> None:
    """
    Browser login is not implemented — no ``/login/`` page exists yet.

    :raises NotImplementedError: until AUTH login screen is built in BPE.
    """
    msg = (
        f"E2E login for role {role!r} is not implemented — "
        "implement once the login page ships (see docs/ux mockups AUTH-LOGIN)."
    )
    logger.info(msg)
    raise NotImplementedError(msg)


@given("the user is not authenticated")
def step_user_not_authenticated(context) -> None:
    """Clear cookies to ensure an anonymous session."""
    context.page.context.clear_cookies()
    logger.info("User is not authenticated (cookies cleared)")
