"""
Munin chat views: HTMX chat panel endpoint (SAO.md §13 — Web layer).

Screen: CHAT-MUNIN-1 (embedded panel in VIEW-BROWSE-1).
POST /chat/munin/  → HTMX partial with Munin's response.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from yggdrasil.graph.models import YggdrasilModel, ensure_c4_metamodel
from yggdrasil.munin.agent import MuninAgent
from yggdrasil.munin.llm_factory import build_munin_planning_llm

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger("yggdrasil.munin")


@method_decorator(csrf_exempt, name="dispatch")
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
        message = (request.POST.get("message") or "").strip()
        if not message and request.body:
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {}
            message = str(payload.get("message") or "").strip()
        if not message:
            return HttpResponseBadRequest("message is required")
        model_id = self._get_model_id(request)
        history = self._parse_history(request)
        llm = self._get_llm_client()
        agent = MuninAgent(llm=llm, model_id=model_id, user_id=request.user.pk)
        logger.info(
            "MuninChatView | post | model_id=%s user=%s",
            model_id,
            request.user.pk,
        )
        response = agent.chat(message, history=history)
        html = self._render_partial(response)
        http = HttpResponse(html, content_type="text/html")
        if response.navigation_url:
            http["HX-Push-Url"] = response.navigation_url
            http["X-Munin-Navigation-Url"] = response.navigation_url
        if response.changeset_id is not None:
            http["X-Munin-Changeset-Id"] = str(response.changeset_id)
        return http

    def _get_llm_client(self):
        """Instantiate the Munin planning-tier LLM client from settings."""
        return build_munin_planning_llm()

    def _get_model_id(self, request: HttpRequest) -> int:
        """Extract model_id from session or query param."""
        raw = request.POST.get("model_id") or request.GET.get("model_id")
        if raw:
            return int(raw)
        session_id = request.session.get("model_id")
        if session_id:
            return int(session_id)
        model = YggdrasilModel.objects.filter(slug="yggdrasil").first()
        if model is None:
            model = YggdrasilModel.objects.create(
                name="Yggdrasil",
                slug="yggdrasil",
                metamodel=ensure_c4_metamodel(),
            )
        return model.pk

    def _parse_history(self, request: HttpRequest) -> list[dict]:
        """Parse conversation history from POST body."""
        raw = request.POST.get("history") or "[]"
        try:
            history = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if not isinstance(history, list):
            return []
        return history

    def _render_partial(self, response) -> str:
        """Render a minimal HTMX chat bubble for the Munin response."""
        cites = "".join(
            f'<li><a href="/elements/{item.get("name", "").lower().replace(" ", "-")}">'
            f'{item.get("name")}</a></li>'
            for item in (response.cited_elements or [])
        )
        nav = (
            f'<div class="munin-nav" data-url="{response.navigation_url}">'
            f"Navigate: {response.navigation_url}</div>"
            if response.navigation_url
            else ""
        )
        return (
            '<div class="munin-response" data-testid="munin-response">'
            f'<div class="munin-text">{response.text}</div>'
            f"{nav}"
            f'<ul class="munin-cites">{cites}</ul>'
            "</div>"
        )
