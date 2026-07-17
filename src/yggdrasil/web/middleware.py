"""
Request-scoped middleware for Yggdrasil.

RequestIdMiddleware — attaches a UUID ``request_id`` to every request
so all log entries for a single HTTP transaction can be correlated.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.web")

REQUEST_ID_HEADER = "X-Request-Id"
REQUEST_ID_ATTR = "request_id"


class RequestIdMiddleware:
    """
    Middleware that assigns a unique request ID to every incoming request.

    The ID is:
    - Read from the ``X-Request-Id`` header if provided by a load balancer.
    - Generated as a UUID4 otherwise.
    - Attached to ``request.request_id`` for use in views and logs.
    - Echoed back in the response header so clients can correlate.

    :param get_response: Django response callable.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.META.get(
            f"HTTP_{REQUEST_ID_HEADER.upper().replace('-', '_')}",
            str(uuid.uuid4()),
        )
        setattr(request, REQUEST_ID_ATTR, request_id)

        logger.debug(
            "request started",
            extra={"request_id": request_id, "method": request.method, "path": request.path},
        )

        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
