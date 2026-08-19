"""
Munin chat views: HTMX chat panel endpoint (SAO.md §13 — Web layer).

Screen: CHAT-MUNIN-1 (embedded panel in VIEW-BROWSE-1).
POST /chat/munin/  → HTMX partial with Munin's response.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from yggdrasil.graph.models import YggdrasilModel, ensure_c4_metamodel
from yggdrasil.munin.agent import MuninAgent, MuninResponse
from yggdrasil.munin.llm_factory import build_munin_planning_llm

if TYPE_CHECKING:
    from django.http import HttpRequest

    from yggdrasil.llm.base import BaseLLM

logger = logging.getLogger("yggdrasil.munin")


@method_decorator(csrf_exempt, name="dispatch")
class MuninChatView(LoginRequiredMixin, View):
    """
    POST /chat/munin/  — process a Munin message and return HTMX partial.

    Body: message (str), history (JSON list[Any] of {role, content} dicts).
    Returns: HTMX partial rendering the Munin response bubble.

    :Example:

    POST /chat/munin/ {message: "Who owns Payment API?", history: []}
    → 200 HTMX partial with response text + cited element links
    """

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """
        :param request: POST with message and history JSON.
        :return: 200 HTMX partial or 400 on validation error.
        :raises ValidationError: If message is blank.
        """
        message = self._read_message(request)
        if not message:
            logger.info("MuninChatView.post | validation | reason=blank_message")
            return HttpResponseBadRequest("message is required")
        model_id = self._get_model_id(request)
        history = self._parse_history(request)
        llm = self._get_llm_client()
        logger.info(
            "MuninChatView.post | entry | model_id=%s user=%s user_pk=%s "
            "message_len=%s history_len=%s llm=%s",
            model_id,
            request.user.pk,
            request.user.pk,
            len(message),
            len(history),
            getattr(llm, "model_id", type(llm).__name__),
        )
        agent = MuninAgent(llm=llm, model_id=model_id, user_id=request.user.pk)
        response = agent.chat(message, history=history)
        logger.info(
            "MuninChatView.post | exit | changeset_id=%s nav=%s",
            response.changeset_id,
            bool(response.navigation_url),
        )
        return self._http_from_munin(response)

    def _read_message(self, request: HttpRequest) -> str:
        """Read message from POST form or JSON body."""
        message = (request.POST.get("message") or "").strip()
        if message or not request.body:
            return message
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = {}
        return str(payload.get("message") or "").strip()

    def _http_from_munin(self, response: MuninResponse) -> HttpResponse:
        """Build HTMX response with optional navigation/changeset headers."""
        http = HttpResponse(self._render_partial(response), content_type="text/html")
        if response.navigation_url:
            http["HX-Push-Url"] = response.navigation_url
            http["X-Munin-Navigation-Url"] = response.navigation_url
        if response.changeset_id is not None:
            http["X-Munin-Changeset-Id"] = str(response.changeset_id)
        return http

    def _get_llm_client(self) -> BaseLLM:
        """Instantiate the Munin planning-tier LLM client from settings."""
        llm = build_munin_planning_llm()
        logger.info(
            "MuninChatView._get_llm_client | branch | reason=factory llm=%s",
            getattr(llm, "model_id", type(llm).__name__),
        )
        return llm

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

    def _parse_history(self, request: HttpRequest) -> list[dict[str, Any]]:
        """Parse conversation history from POST body."""
        raw = request.POST.get("history") or "[]"
        try:
            history = json.loads(raw)
        except json.JSONDecodeError:
            logger.info("MuninChatView._parse_history | branch | reason=invalid_json")
            return []
        if not isinstance(history, list):
            logger.info("MuninChatView._parse_history | branch | reason=not_list")
            return []
        logger.info(
            "MuninChatView._parse_history | exit | history_len=%s",
            len(history),
        )
        return history

    def _render_partial(self, response: MuninResponse) -> str:
        """Render a minimal HTMX chat bubble for the Munin response."""
        cites = "".join(
            f'<li><a href="/elements/{item.get("name", "").lower().replace(" ", "-")}">'
            f"{item.get('name')}</a></li>"
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
