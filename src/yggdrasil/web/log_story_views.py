"""DEBUG-only request log story viewer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_GET

from yggdrasil.web.log_story import load_recent_requests, load_request_story

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.web")


@require_GET
def request_log_story(request: HttpRequest) -> HttpResponse:
    """
    Render the local request-story viewer (DEBUG only).

    :param request: Incoming request. Query ``request_id`` selects a story.
    :return: HTML story page.
    :raises Http404: When ``DEBUG`` is false.
    """
    if not settings.DEBUG:
        raise Http404("Log story viewer is DEBUG-only")
    log_path = settings.LOGS_DIR / "app.log"
    requests = load_recent_requests(log_path)
    request_id = (request.GET.get("request_id") or "").strip()
    if not request_id and requests:
        request_id = str(requests[0]["request_id"])
    story = load_request_story(log_path, request_id) if request_id else None
    logger.info(
        "request_log_story | entry | request_id=%s request_count=%s has_story=%s",
        request_id or "(none)",
        len(requests),
        bool(story),
    )
    return render(
        request,
        "web/log_story.html",
        {
            "requests": requests,
            "selected_id": request_id,
            "story": story,
        },
    )
