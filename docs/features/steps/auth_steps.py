"""
Auth AT steps (Django test client + UserFactory).

Steps:
  - Given the user is logged in as "{role}"
  - Given the user is not authenticated
"""

from __future__ import annotations

import logging

from behave import given
from steps.common_steps import get_client
from tests.fixtures.factories import UserFactory

logger = logging.getLogger(__name__)

_ROLE_TRAITS: dict[str, str] = {
    "admin": "is_admin",
    "architect": "is_architect",
    "viewer": "is_viewer",
}


@given('the user is logged in as "{role}"')
def step_user_logged_in_as(context, role: str) -> None:
    """Create a user with the given RBAC role and force-login via test client."""
    trait = _ROLE_TRAITS.get(role)
    assert trait, f"Unknown role {role!r}; expected one of {list(_ROLE_TRAITS)}"
    user = UserFactory(**{trait: True})
    password = "test-pass-only-1234"
    user.set_password(password)
    user.save()
    get_client(context).force_login(user)
    context.current_user = user
    logger.info("User logged in as %s (%s)", role, user.username)


@given("the user is not authenticated")
def step_user_not_authenticated(context) -> None:
    """Ensure no session is active on the test client."""
    get_client(context).logout()
    context.current_user = None
    logger.info("User is not authenticated")
