"""
Web views for Yggdrasil.

/health/ — machine-readable liveness probe (no auth required).
/        — welcome page.
/views/  — VIEW-BROWSE-1 (authenticated).
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from yggdrasil.graph import browse_service
from yggdrasil.graph.models import Element, Relationship
from yggdrasil.web.browse_helpers import (
    build_view_browse_context,
    enrich_confidence_fields,
    parse_view_browse_params,
)

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

    Renders filter panel and element results from ``browse_service``.
    """

    template_name = "web/view/browse.html"
    partial_template_name = "web/view/partials/results.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Render the View Browser page or HTMX results partial.

        :param request: Authenticated GET request.
        :return: Full page or partial HTML with filtered elements.
        """
        params = parse_view_browse_params(request)
        context = build_view_browse_context(request, params)
        logger.info(
            "ViewBrowseView.get | user_pk=%s element_count=%s package=%s stereotype=%s",
            request.user.pk,
            context["element_count"],
            params.package,
            params.stereotype,
        )
        if request.headers.get("HX-Request"):
            return render(request, self.partial_template_name, context)
        return render(request, self.template_name, context)


class ViewBrowseGraphJsonView(LoginRequiredMixin, View):
    """GET /views/graph.json — Cytoscape subgraph for current filters."""

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        Return filtered subgraph JSON for graph mode.

        :param request: Authenticated GET request with optional filter query params.
        :return: JSON ``{"elements": [...], "edges": [...]}``.
        """
        params = parse_view_browse_params(request)
        payload = browse_service.subgraph_for_elements(
            model_slug=params.model_slug,
            stereotype=params.stereotype,
            package=params.package,
            health=params.health,
            user_id=request.user.pk,
        )
        logger.info(
            "ViewBrowseGraphJsonView.get | user_pk=%s nodes=%s edges=%s",
            request.user.pk,
            len(payload["elements"]),
            len(payload["edges"]),
        )
        return JsonResponse(payload)


class ViewBrowseInspectorElementView(LoginRequiredMixin, View):
    """GET /views/inspector/element/<pk>/ — element embed partial for inspector."""

    template_name = "web/view/partials/inspector_element.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Render element properties for the View Browser inspector panel.

        :param request: Authenticated GET request.
        :param pk: Element primary key.
        :return: HTML partial without page chrome.
        """
        try:
            payload = browse_service.get_element_for_inspector(pk, user_id=request.user.pk)
        except Element.DoesNotExist as exc:
            raise Http404("Element not found") from exc
        element = enrich_confidence_fields(payload["element"])
        context = {
            "element": element,
            "relationships": payload["relationships"],
            "relationships_in": payload["relationships_in"],
            "relationships_out": payload["relationships_out"],
        }
        logger.info(
            "ViewBrowseInspectorElementView.get | user_pk=%s element_id=%s rel_count=%s",
            request.user.pk,
            pk,
            len(payload["relationships"]),
        )
        return render(request, self.template_name, context)


class ViewBrowseInspectorRelationshipView(LoginRequiredMixin, View):
    """GET /views/inspector/relationship/<pk>/ — relationship embed partial for inspector."""

    template_name = "web/view/partials/inspector_relationship.html"

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        """
        Render relationship properties for the View Browser inspector panel.

        :param request: Authenticated GET request.
        :param pk: Relationship primary key.
        :return: HTML partial without page chrome.
        """
        try:
            detail = browse_service.get_relationship_for_inspector(pk, user_id=request.user.pk)
        except Relationship.DoesNotExist as exc:
            raise Http404("Relationship not found") from exc
        relationship = enrich_confidence_fields(detail)
        logger.info(
            "ViewBrowseInspectorRelationshipView.get | user_pk=%s relationship_id=%s",
            request.user.pk,
            pk,
        )
        return render(request, self.template_name, {"relationship": relationship})
