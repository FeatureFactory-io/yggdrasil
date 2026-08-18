"""
Web views for Yggdrasil.

/health/ — machine-readable liveness probe (no auth required).
/        — welcome page.
/views/  — VIEW-BROWSE-1 (authenticated).
"""

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from yggdrasil.graph import browse_service, browse_view_service
from yggdrasil.graph.models import BrowseView, Element, Relationship
from yggdrasil.web.browse_helpers import (
    apply_browse_view_expansion,
    build_empty_browse_context,
    build_payload_from_browse_params,
    build_view_browse_context,
    enrich_confidence_fields,
    parse_browse_params_from_post,
    parse_view_browse_params,
    user_can_save_views,
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
    navigator_partial_template_name = "web/view/partials/navigator_tree.html"

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
        params = apply_browse_view_expansion(request, request.user, ymodel, params)
        if params.browse_view:
            logger.info(
                "ViewBrowseView.get | branch | browse_view=%s expanded=%s loaded_view_name=%s",
                params.browse_view,
                bool(params.loaded_view_name),
                params.loaded_view_name or "",
            )
        context = build_view_browse_context(request, params)
        if request.GET.get("partial") == "navigator":
            logger.info(
                "ViewBrowseView.get | partial=navigator | user_pk=%s depth=%s",
                request.user.pk,
                params.depth,
            )
            return render(request, self.navigator_partial_template_name, context)
        if request.GET.get("partial") == "results":
            logger.info(
                "ViewBrowseView.get | partial=results | user_pk=%s element_count=%s",
                request.user.pk,
                context["element_count"],
            )
            return render(request, self.partial_template_name, context)
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
            "ViewBrowseView.get | exit | user_pk=%s element_count=%s depth=%s package=%s stereotype=%s",
            request.user.pk,
            context["element_count"],
            params.depth,
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
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc
        params = parse_view_browse_params(request, model_slug)
        params = apply_browse_view_expansion(request, request.user, ymodel, params)
        payload = browse_service.subgraph_for_elements(
            model_slug=params.model_slug,
            stereotype=params.stereotype,
            package=params.package,
            health=params.health,
            depth=params.depth,
            user_id=request.user.pk,
        )
        logger.info(
            "ViewBrowseGraphJsonView.get | user_pk=%s depth=%s nodes=%s edges=%s",
            request.user.pk,
            params.depth,
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


class ViewBrowseSaveView(LoginRequiredMixin, View):
    """POST /models/{slug}/views/save/ — persist current browse session as a named View."""

    def post(self, request: HttpRequest, model_slug: str) -> HttpResponse:
        """
        Save filters, depth, and presentation mode as a BrowseView snapshot.

        :param request: Authenticated POST with ``name`` and current filter fields.
        :param model_slug: Model slug from the URL path.
        :return: Redirect to ``?browse_view={slug}`` on success.
        """
        logger.info(
            "ViewBrowseSaveView.post | entry | user_pk=%s model_slug=%s",
            request.user.pk,
            model_slug,
        )
        if not user_can_save_views(request.user):
            logger.info(
                "ViewBrowseSaveView.post | validation | user_pk=%s reason=not_architect",
                request.user.pk,
            )
            raise Http404("Not found")
        try:
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc

        name = (request.POST.get("name") or "").strip()
        params = parse_browse_params_from_post(request, model_slug)
        payload = build_payload_from_browse_params(params)
        try:
            saved = browse_view_service.save_view(
                request.user,
                ymodel,
                name=name,
                payload=payload,
            )
        except ValidationError as exc:
            logger.info(
                "ViewBrowseSaveView.post | validation | user_pk=%s model_slug=%s reason=%s",
                request.user.pk,
                model_slug,
                exc.message_dict,
            )
            return redirect(reverse("web:view_browse_model", kwargs={"model_slug": model_slug}))

        location = (
            reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
            + f"?browse_view={saved.slug}"
        )
        logger.info(
            "ViewBrowseSaveView.post | exit | user_pk=%s model_slug=%s slug=%s",
            request.user.pk,
            model_slug,
            saved.slug,
        )
        return redirect(location)


class ViewBrowseDeleteView(LoginRequiredMixin, View):
    """POST /models/{slug}/views/{view_slug}/delete/ — owner-only View removal."""

    def post(self, request: HttpRequest, model_slug: str, view_slug: str) -> HttpResponse:
        """
        Delete a saved View owned by the current user.

        :param request: Authenticated POST request.
        :param model_slug: Model slug from the URL path.
        :param view_slug: Saved View slug to delete.
        :return: Redirect to unfiltered browse URL.
        """
        logger.info(
            "ViewBrowseDeleteView.post | entry | user_pk=%s model_slug=%s view_slug=%s",
            request.user.pk,
            model_slug,
            view_slug,
        )
        if not user_can_save_views(request.user):
            raise Http404("Not found")
        try:
            ymodel = browse_service.user_can_read_model(request.user, model_slug)
        except (ValueError, PermissionError) as exc:
            raise Http404("Model not found") from exc
        try:
            browse_view_service.delete_view(request.user, ymodel, view_slug)
        except PermissionError as exc:
            logger.info(
                "ViewBrowseDeleteView.post | validation | user_pk=%s view_slug=%s reason=not_owner",
                request.user.pk,
                view_slug,
            )
            raise Http404("Not found") from exc
        except BrowseView.DoesNotExist as exc:
            raise Http404("View not found") from exc

        location = reverse("web:view_browse_model", kwargs={"model_slug": model_slug})
        logger.info(
            "ViewBrowseDeleteView.post | exit | user_pk=%s model_slug=%s view_slug=%s",
            request.user.pk,
            model_slug,
            view_slug,
        )
        return redirect(location)
