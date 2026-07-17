"""
Munin chat views: HTMX chat panel endpoint (SAO.md §13 — Web layer).

Screen: CHAT-MUNIN-1 (embedded panel in VIEW-BROWSE-1).
POST /chat/munin/  → HTMX partial with Munin's response.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.munin")


class MuninChatView(LoginRequiredMixin, View):
    """
    POST /chat/munin/  — process a Munin message and return HTMX partial.

    Body: message (str), history (JSON list of {role, content} dicts).
    Returns: HTMX partial rendering the Munin response bubble.

    :Example:

    POST /chat/munin/ {message: "Who owns Payment API?", history: []}
    → 200 HTMX partial with response text + cited element links
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        :param request: POST with message and history JSON.
        :return: 200 HTMX partial or 400 on validation error.
        :raises ValidationError: If message is blank.
        """
        raise NotImplementedError()

    def _get_llm_client(self):
        """Instantiate the LLM client based on LLM_PROVIDER setting."""
        raise NotImplementedError()

    def _get_model_id(self, request: HttpRequest) -> int:
        """Extract model_id from session or query param."""
        raise NotImplementedError()

    def _parse_history(self, request: HttpRequest) -> list[dict]:
        """Parse conversation history from POST body."""
        raise NotImplementedError()
