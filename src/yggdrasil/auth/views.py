"""
Auth views: session login/logout and personal access token management.

All views delegate business logic to ``TokenService`` (SAO.md §3).
Templates live in ``web/templates/`` (mockup) and ``auth/templates/``
(real) — same template names, swapped by app order in INSTALLED_APPS.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from yggdrasil.auth.services import TokenService

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.auth")

_DEFAULT_REDIRECT = "/"


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
        """
        Render the login form, or redirect if the user is already authenticated.

        :param request: Incoming HTTP request.
        :return: 200 with login template, or 302 redirect to dashboard.

        :Example:

        GET /auth/login/ (unauthenticated) → 200 login form
        GET /auth/login/ (authenticated)   → 302 to dashboard
        """
        logger.info(
            "LoginView.get: entry | ip=%s authenticated=%s",
            request.META.get("REMOTE_ADDR"),
            request.user.is_authenticated,
        )
        if request.user.is_authenticated:
            logger.info("LoginView.get: user already authenticated, redirecting")
            return self._redirect_after_login(request)
        logger.info("LoginView.get: rendering login form")
        return render(request, self.template_name)

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Validate credentials and start a session.

        Calls Django's ``authenticate()`` (never raw ORM) so pluggable
        backends remain supported.  Session key is rotated by ``login()``
        to prevent session fixation.

        :param request: Incoming POST request with ``email`` and ``password``.
        :return: 302 redirect on success; 200 re-render with error on failure.
        :raises N/A: Never raises — form errors are rendered in place.

        :Example:

        POST /auth/login/ email=elena@example.com password=… → 302 /
        POST /auth/login/ email=bad@example.com password=wrong → 200 (error)
        """
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        logger.info(
            "LoginView.post: attempt | email=%s ip=%s",
            email,
            request.META.get("REMOTE_ADDR"),
        )
        user = authenticate(request, username=email, password=password)
        if user is None:
            logger.warning("LoginView.post: authentication failed | email=%s", email)
            return render(
                request,
                self.template_name,
                {"error": "Invalid email or password."},
            )
        login(request, user)
        logger.info("LoginView.post: login success | user_pk=%s", user.pk)
        return self._redirect_after_login(request)

    def _redirect_after_login(self, request: HttpRequest) -> HttpResponse:
        """
        Redirect to the ``next`` query parameter or the default dashboard.

        :param request: Incoming HTTP request; may contain ``?next=`` param.
        :return: HTTP 302 redirect response.

        :Example:

        ?next=/graph/ → redirect to /graph/
        (no next)     → redirect to /
        """
        next_url = request.POST.get("next") or request.GET.get("next", _DEFAULT_REDIRECT)
        if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
            next_url = _DEFAULT_REDIRECT
        logger.info("LoginView._redirect_after_login: redirecting to %s", next_url)
        return redirect(next_url)


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
        """
        Render the token management page with the authenticated user's tokens.

        Delegates to :meth:`TokenService.list_tokens` — never queries ORM
        directly (SAO.md §3 layer separation).  ``token_hash`` is NOT passed
        to the template.

        :param request: Incoming authenticated GET request.
        :return: 200 response with ``tokens`` QuerySet in context.

        :Example:

        GET /auth/tokens/ (authenticated) → 200, renders auth/token.html
        """
        tokens = TokenService().list_tokens(request.user)
        logger.info(
            "TokenListView.get | user_pk=%s token_count=%d",
            request.user.pk,
            tokens.count(),
        )
        return render(request, self.template_name, {"tokens": tokens})


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
