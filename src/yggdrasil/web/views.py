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
    build_empty_browse_context,
    build_view_browse_context,
    enrich_confidence_fields,
    parse_view_browse_params,
)

logger = logging.getLogger("yggdrasil.web")

MODEL_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


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


class ViewBrowseRedirectView(LoginRequiredMixin, View):
    """
    GET /views/ — unscoped alias redirecting to the default Model browse URL.

    When the user can read zero Models, renders an empty-state page instead.
    """

    template_name = "web/view/browse.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Redirect to canonical browse URL or render zero-model empty state.

        :param request: Authenticated GET request.
        :return: 302 redirect or empty-state HTML.
        """
        logger.info("ViewBrowseRedirectView.get | entry | user_pk=%s", request.user.pk)
        cookie_value = request.COOKIES.get(browse_service.MODEL_COOKIE_NAME)
        default_slug = browse_service.resolve_default_model_slug(request.user, cookie_value)
        if default_slug is None:
            logger.info(
                "ViewBrowseRedirectView.get | branch | user_pk=%s empty_state=true",
                request.user.pk,
            )
            return render(request, self.template_name, build_empty_browse_context(request))
        location = reverse("web:view_browse_model", kwargs={"model_slug": default_slug})
        query_string = request.META.get("QUERY_STRING", "")
        if query_string:
            location = f"{location}?{query_string}"
        logger.info(
            "ViewBrowseRedirectView.get | exit | user_pk=%s location=%s model_slug=%s",
            request.user.pk,
            location,
            default_slug,
        )
        return redirect(location)


class ViewBrowseView(LoginRequiredMixin, View):
    """
    GET /models/{slug}/views/ — VIEW-BROWSE-1 View Browser.

    Renders filter panel and element results from ``browse_service``.
    """

    template_name = "web/view/browse.html"
    partial_template_name = "web/view/partials/results.html"

    def get(self, request: HttpRequest, model_slug: str) -> HttpResponse:
        """
        Render the View Browser page or HTMX results partial.

        :param request: Authenticated GET request.
        :param model_slug: Model slug from the URL path.
        :return: Full page or partial HTML with filtered elements.
        """
        logger.info(
            "ViewBrowseView.get | entry | user_pk=%s model_slug=%s",
            request.user.pk,
            model_slug,
        )
        try:
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
        except ValueError as exc:
            logger.info(
                "ViewBrowseView.get | validation | user_pk=%s model not found slug=%s",
                request.user.pk,
                model_slug,
            )
            raise Http404("Model not found") from exc
        except PermissionError as exc:
            logger.info(
                "ViewBrowseView.get | validation | user_pk=%s model not readable slug=%s",
                request.user.pk,
                model_slug,
            )
            raise Http404("Model not found") from exc

        params = parse_view_browse_params(request, model_slug)
        context = build_view_browse_context(request, params)
        template = (
            self.partial_template_name if request.headers.get("HX-Request") else self.template_name
        )
        response = render(request, template, context)
        response.set_cookie(
            browse_service.MODEL_COOKIE_NAME,
            ymodel.slug,
            max_age=MODEL_COOKIE_MAX_AGE,
        )
        request.session["model_id"] = ymodel.pk
        request.session.modified = True
        logger.info(
            "ViewBrowseView.get | processing | user_pk=%s cookie=%s model_slug=%s",
            request.user.pk,
            browse_service.MODEL_COOKIE_NAME,
            ymodel.slug,
        )
        logger.info(
            "ViewBrowseView.get | exit | user_pk=%s element_count=%s package=%s stereotype=%s",
            request.user.pk,
            context["element_count"],
            params.package,
            params.stereotype,
        )
        return response


class ViewBrowseGraphJsonView(LoginRequiredMixin, View):
    """GET /models/{slug}/views/graph.json — Cytoscape subgraph for current filters."""

    def get(self, request: HttpRequest, model_slug: str) -> JsonResponse:
        """
        Return filtered subgraph JSON for graph mode.

        :param request: Authenticated GET request with optional filter query params.
        :param model_slug: Model slug from the URL path.
        :return: JSON ``{"elements": [...], "edges": [...]}``.
        """
        try:
            browse_service.user_can_read_model(request.user, model_slug)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc
        params = parse_view_browse_params(request, model_slug)
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
    """GET /models/{slug}/views/inspector/element/<pk>/ — element embed partial."""

    template_name = "web/view/partials/inspector_element.html"

    def get(self, request: HttpRequest, model_slug: str, pk: int) -> HttpResponse:
        """
        Render element properties for the View Browser inspector panel.

        :param request: Authenticated GET request.
        :param model_slug: Model slug from the URL path.
        :param pk: Element primary key.
        :return: HTML partial without page chrome.
        """
        try:
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
            Element.objects.get(pk=pk, model=ymodel)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc
        except Element.DoesNotExist as exc:
            raise Http404("Element not found") from exc
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
    """GET /models/{slug}/views/inspector/relationship/<pk>/ — relationship embed."""

    template_name = "web/view/partials/inspector_relationship.html"

    def get(self, request: HttpRequest, model_slug: str, pk: int) -> HttpResponse:
        """
        Render relationship properties for the View Browser inspector panel.

        :param request: Authenticated GET request.
        :param model_slug: Model slug from the URL path.
        :param pk: Relationship primary key.
        :return: HTML partial without page chrome.
        """
        try:
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc
        try:
            detail = browse_service.get_relationship_for_inspector(pk, user_id=request.user.pk)
        except Relationship.DoesNotExist as exc:
            raise Http404("Relationship not found") from exc
        if not Relationship.objects.filter(pk=pk, model=ymodel).exists():
            raise Http404("Relationship not found")
        relationship = enrich_confidence_fields(detail)
        logger.info(
            "ViewBrowseInspectorRelationshipView.get | user_pk=%s relationship_id=%s",
            request.user.pk,
            pk,
        )
        return render(request, self.template_name, {"relationship": relationship})
