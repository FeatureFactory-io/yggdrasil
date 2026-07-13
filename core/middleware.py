"""GUI interaction logging middleware."""

import logging

logger = logging.getLogger("yggdrasil.gui")


class GuiLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(("/", "elements", "views", "chat", "changesets")):
            logger.info(
                "path=%s method=%s status=%d user=%s",
                request.path,
                request.method,
                response.status_code,
                getattr(request.user, "username", "anonymous"),
            )
        return response
