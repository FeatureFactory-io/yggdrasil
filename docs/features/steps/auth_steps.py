"""
Auth AT steps (Django test client + UserFactory).

Steps:
  - Given the user is logged in as "{role}"
  - Given the user is not authenticated
  - Given a user exists with email "{email}" and password "{password}"
  - Given the user has a token named "{name}" with scope "{scope}"
  - When I POST "/auth/login/" with email "{email}" and password "{password}"
  - When I POST "/auth/tokens/create/" with name "{name}" and scope "{scope}"
"""

from __future__ import annotations

import logging

from behave import given, then, when
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


@given('a user exists with email "{email}" and password "{password}"')
def step_user_exists_with_credentials(context, email: str, password: str) -> None:
    """
    Create a real User with the given email/password (no session).

    Username is set to the email so Django's default auth backend accepts
    ``authenticate(username=email)`` as well as email lookup.
    """
    user = UserFactory(email=email, username=email)
    user.set_password(password)
    user.save()
    context.seed_user = user
    logger.info("Created user email=%s username=%s", email, user.username)


@when('I POST "/auth/login/" with email "{email}" and password "{password}"')
def step_post_login(context, email: str, password: str) -> None:
    """POST credentials to the real LoginView and store the response."""
    response = get_client(context).post(
        "/auth/login/",
        {"email": email, "password": password},
    )
    context.response = response
    logger.info(
        "POST /auth/login/ email=%s status=%s location=%s",
        email,
        response.status_code,
        response.get("Location", ""),
    )


@then('the response redirects away from "{path}"')
def step_response_redirects_away(context, path: str) -> None:
    """Assert 3xx Location is set and does not point at ``path``."""
    response = context.response
    assert 300 <= response.status_code < 400, f"Expected redirect, got {response.status_code}"
    location = response.get("Location", "")
    assert location, "Redirect response has no Location header"
    assert not location.startswith(path), f"Expected redirect away from {path!r}, got {location!r}"
    logger.info("Redirected away from %s → %s", path, location)


@then('the response Location contains "{fragment}"')
def step_response_location_contains(context, fragment: str) -> None:
    """Assert the redirect Location header contains ``fragment``."""
    location = context.response.get("Location", "")
    assert fragment in location, f"Expected {fragment!r} in Location {location!r}"
    logger.info("Location contains %s → %s", fragment, location)


@given('the user has a token named "{name}" with scope "{scope}"')
def step_user_has_token(context, name: str, scope: str) -> None:
    """Create a real PersonalAccessToken for the current user via TokenService."""
    from yggdrasil.auth.services import TokenService

    user = context.current_user
    assert user, "No current user — call 'the user is logged in as' first"
    token, raw = TokenService().create_token(user, name, scope)
    context.last_token = token
    context.last_token_raw = raw
    logger.info("Created token pk=%s name=%s scope=%s", token.pk, name, scope)


@when('I POST "/auth/tokens/create/" with name "{name}" and scope "{scope}"')
def step_post_token_create(context, name: str, scope: str) -> None:
    """POST to the real token create endpoint and store the response."""
    client = get_client(context)
    response = client.post(
        "/auth/tokens/create/",
        {"name": name, "scope": scope},
    )
    context.response = response
    logger.info(
        "POST /auth/tokens/create/ name=%s scope=%s status=%s", name, scope, response.status_code
    )
