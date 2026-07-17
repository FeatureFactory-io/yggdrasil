"""
Web views for Yggdrasil.

/health/ — machine-readable liveness probe (no auth required).
/        — welcome page.
"""

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse
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
    Welcome / landing page.

    :param request: Django HTTP request.
    :return: Rendered HTML response.
    """
    logger.debug("index requested", extra={"user": str(request.user)})
    from django.shortcuts import render

    return render(request, "web/index.html")
