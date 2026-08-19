"""
Request-scoped middleware for Yggdrasil.

RequestIdMiddleware — attaches a UUID ``request_id`` to every request
so all log entries for a single HTTP transaction can be correlated.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from yggdrasil.log_context import bind_request_context, clear_request_context

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.web")

REQUEST_ID_HEADER = "X-Request-Id"
REQUEST_ID_ATTR = "request_id"
_HEADER_META_KEY = f"HTTP_{REQUEST_ID_HEADER.upper().replace('-', '_')}"


class RequestIdMiddleware:
    """
    Middleware that assigns a unique request ID to every incoming request.

    The ID is:
    - Read from the ``X-Request-Id`` header if provided by a load balancer.
    - Generated as a UUID4 otherwise.
    - Attached to ``request.request_id`` for use in views and logs.
    - Bound into log contextvars so every Yggdrasil log line shares it.
    - Echoed back in the response header so clients can correlate.

    :param get_response: Django response callable.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = self._resolve_request_id(request)
        setattr(request, REQUEST_ID_ATTR, request_id)
        self._bind_context(request, request_id)
        started = time.perf_counter()
        logger.info(
            "RequestIdMiddleware | entry | request started | method=%s path=%s",
            request.method,
            request.path,
        )
        try:
            response = self.get_response(request)
        except Exception:
            logger.exception(
                "RequestIdMiddleware | error | request failed | method=%s path=%s",
                request.method,
                request.path,
            )
            raise
        else:
            self._log_exit(request, response, started)
            response[REQUEST_ID_HEADER] = request_id
            return response
        finally:
            clear_request_context()

    def _resolve_request_id(self, request: HttpRequest) -> str:
        """
        Reuse an inbound request id or generate a UUID4.

        :param request: Incoming Django request.
        :return: Non-empty request id. Example: ``"7f3a9b2c-4e1d-4a6b-9c0f-1a2b3c4d5e6f"``.
        """
        inbound = (request.META.get(_HEADER_META_KEY) or "").strip()
        return inbound or str(uuid.uuid4())

    def _bind_context(self, request: HttpRequest, request_id: str) -> None:
        """Bind correlation fields; replace any leftover context from a prior request."""
        clear_request_context()
        fields: dict[str, object] = {
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
        }
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            fields["user_id"] = user.pk
        bind_request_context(**fields)

    def _log_exit(
        self,
        request: HttpRequest,
        response: HttpResponse,
        started: float,
    ) -> None:
        """Log request completion while contextvars are still bound."""
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "RequestIdMiddleware | exit | request completed | "
            "method=%s path=%s status_code=%s duration_ms=%.2f",
            request.method,
            request.path,
            response.status_code,
            duration_ms,
        )
