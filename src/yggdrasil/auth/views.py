"""
Auth views: session login/logout and personal access token management.

All views delegate business logic to ``TokenService`` (SAO.md §3).
Templates live in ``web/templates/`` (mockup) and ``auth/templates/``
(real) — same template names, swapped by app order in INSTALLED_APPS.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.auth")


class LoginView(View):
    """
    GET  /auth/login/  — render login form.
    POST /auth/login/  — authenticate and redirect.

    :Example:

    On success: redirect to ``VIEW-BROWSE-1`` (``/``).
    On failure: re-render form with error message.
    """

    template_name = "auth/login.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render login form. Redirect to dashboard if already authenticated."""
        raise NotImplementedError()

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Validate credentials and start session.

        :raises N/A: Never raises — form errors are rendered in place.
        """
        raise NotImplementedError()

    def _redirect_after_login(self, request: HttpRequest) -> HttpResponse:
        """Redirect to ``next`` param or default dashboard."""
        raise NotImplementedError()


class LogoutView(LoginRequiredMixin, View):
    """POST /auth/logout/ — terminate session."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """Log out and redirect to login page."""
        raise NotImplementedError()


class TokenListView(LoginRequiredMixin, View):
    """
    GET /auth/tokens/ — list personal access tokens for the current user.

    Screen: AUTH-TOKEN-1
    """

    template_name = "auth/token.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render token management page with existing tokens."""
        raise NotImplementedError()


class TokenCreateView(LoginRequiredMixin, View):
    """POST /auth/tokens/create/ — generate a new token (shown once)."""

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Create token, surface the raw value in a one-time response.

        :raises ValueError: If scope is invalid (returns 400).
        """
        raise NotImplementedError()


class TokenRevokeView(LoginRequiredMixin, View):
    """POST /auth/tokens/<token_id>/revoke/ — delete a token."""

    def post(self, request: HttpRequest, token_id: int) -> HttpResponse:
        """
        Permanently revoke *token_id* owned by the current user.

        :param token_id: PK of the token to revoke.
        :raises PermissionError: If token belongs to another user (returns 403).
        """
        raise NotImplementedError()
