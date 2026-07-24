"""
Web views for Yggdrasil.

/health/ — machine-readable liveness probe (no auth required).
/        — welcome page.
/views/  — VIEW-BROWSE-1 (authenticated).
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger("yggdrasil.web")


@never_cache
@require_GET
def health(request: HttpRequest) -> JsonResponse:
    """
    Liveness probe for EB / load-balancer health checks.

    Returns HTTP 200 with ``{"status": "ok"}`` when Django is running.
    No database or Redis calls are made — intentionally shallow.

    :param request: Django HTTP request.
    :return: JSON response ``{"status": "ok"}``.
    """
    logger.debug("health check requested", extra={"path": request.path})
    return JsonResponse({"status": "ok"})


@require_GET
def index(request: HttpRequest) -> HttpResponse:
    """
    Welcome / landing page for anonymous visitors.

    Authenticated users are sent to ``VIEW-BROWSE-1`` (``/views/``).

    :param request: Django HTTP request.
    :return: Rendered HTML for anonymous users, or redirect for authenticated.
    """
    if request.user.is_authenticated:
        logger.info(
            "index: authenticated user redirecting to view browser | user_pk=%s",
            request.user.pk,
        )
        return redirect(reverse("web:view_browse"))

    logger.debug("index requested", extra={"user": str(request.user)})
    return render(request, "web/index.html")


class ViewBrowseView(LoginRequiredMixin, View):
    """
    GET /views/ — VIEW-BROWSE-1 View Browser.

    Renders the production shell with an empty element list until
    ``GraphBrowseService`` lands (Act 2). Layout and testids follow the mockup.
    """

    template_name = "web/view/browse.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Render the View Browser shell (filters + empty results table).

        :param request: Authenticated GET request.
        :return: 200 with filter panel and empty element table.
        """
        logger.info(
            "ViewBrowseView.get | user_pk=%s element_count=0",
            request.user.pk,
        )
        return render(request, self.template_name, {"elements": []})
