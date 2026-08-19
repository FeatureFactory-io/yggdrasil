"""
ChangeSet views: list[Any], detail, approve/reject/do-other/rollback actions.

All mutating actions delegate to ChangeSetService (SAO.md §3 — layer separation).
Views never call ORM directly.

Screen IDs (docs/ux/2_dialogue-maps/screen-flow.md):
  CHANGESET-LIST+FIND-1  → ChangeSetListView (GET /changesets/)
  CHANGESET-VIEW_CHANGESET-1 → ChangeSetDetailView (GET /changesets/<id>/)

HTMX partials returned for approve/reject/do-other/rollback actions.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.views import View

from yggdrasil.changeset.services import ChangeSetService

if TYPE_CHECKING:
    from django.http import HttpRequest

logger = logging.getLogger("yggdrasil.changeset")

_service = ChangeSetService()


def _story(where: str, beat: str, *, level: int = logging.INFO, **fields: object) -> None:
    """Emit a grep-friendly log story line: ``Class.method | beat | key=value``."""
    payload = " ".join(f"{key}={value}" for key, value in fields.items())
    if payload:
        logger.log(level, "%s | %s | %s", where, beat, payload)
        return
    logger.log(level, "%s | %s", where, beat)


def _user_pk(request: HttpRequest) -> int | None:
    """Return the authenticated user's PK, or None."""
    return getattr(getattr(request, "user", None), "pk", None)


def _parse_item_ids(request: HttpRequest, *, where: str) -> list[int] | None:
    """Parse optional item_ids from POST; None means all pending items."""
    raw = request.POST.get("item_ids")
    if raw is None:
        _story(where, "branch", reason="all_items")
        return None
    try:
        values = json.loads(raw) if raw.strip().startswith("[") else raw.split(",")
        ids = [int(value) for value in values if str(value).strip() != ""]
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        _story(where, "error", reason="bad_item_ids", raw=raw, level=logging.ERROR)
        msg = "invalid item_ids"
        raise ValueError(msg) from exc
    _story(where, "branch", reason="item_ids_filter", item_ids=ids)
    return ids


class ChangeSetListView(LoginRequiredMixin, View):
    """
    GET /changesets/  — list[Any] all ChangeSets with status/source filters.

    Query params: ?status=pending|applied|rejected, ?source=ratatosk|human|mcp
    :Example: GET /changesets/?status=pending → 200 with filtered list[Any]
    """

    template_name = "changeset/list[Any].html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        :param request: GET request with optional ?status and ?source params.
        :return: 200 rendered list[Any] page.
        """
        _story("ChangeSetListView.get", "entry", user_pk=_user_pk(request))
        filters = self._get_filter_params(request)
        status = filters.get("status") or ""
        source = filters.get("source") or ""
        if status:
            reason = "status_filter"
        elif source:
            reason = "source_filter"
        else:
            reason = "no_filter"
        _story(
            "ChangeSetListView.get",
            "branch",
            reason=reason,
            status=status,
            source=source,
        )
        raise NotImplementedError()

    def _get_filter_params(self, request: HttpRequest) -> dict[str, Any]:
        """Extract and validate status/source query parameters."""
        status = request.GET.get("status")
        source = request.GET.get("source")
        if status:
            _story(
                "ChangeSetListView._get_filter_params",
                "branch",
                reason="status_filter",
                status=status,
            )
        if source:
            _story(
                "ChangeSetListView._get_filter_params",
                "branch",
                reason="source_filter",
                source=source,
            )
        if not status and not source:
            _story("ChangeSetListView._get_filter_params", "branch", reason="no_filter")
        return {"status": status, "source": source}


class ChangeSetDetailView(LoginRequiredMixin, View):
    """
    GET /changesets/<id>/  — view a single ChangeSet with all operations.

    :Example: GET /changesets/1/ → 200 with operation rows and bulk action buttons
    """

    template_name = "changeset/view.html"

    def get(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: Incoming request.
        :param changeset_id: ChangeSet PK. Example: 1
        :return: 200 rendered detail page.
        :raises Http404: If ChangeSet not found.
        """
        _story(
            "ChangeSetDetailView.get",
            "entry",
            user_pk=_user_pk(request),
            changeset_id=changeset_id,
        )
        raise NotImplementedError()


class ChangeSetApproveView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/approve/  — apply pending operations.

    Body: item_ids (optional JSON list[Any]) — omit to approve all.
    Returns HTMX partial updating the operation rows.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST with optional item_ids JSON body.
        :param changeset_id: ChangeSet PK.
        :return: HTMX partial with updated operation rows.
        :raises Http404: If ChangeSet not found.
        """
        _story(
            "ChangeSetApproveView.post",
            "entry",
            user_pk=_user_pk(request),
            changeset_id=changeset_id,
        )
        try:
            item_ids = self._parse_item_ids(request)
        except ValueError:
            _story(
                "ChangeSetApproveView.post",
                "error",
                reason="bad_item_ids",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise
        _story(
            "ChangeSetApproveView.post",
            "branch",
            reason="all_items" if item_ids is None else "item_ids_filter",
            item_ids=item_ids,
        )
        raise NotImplementedError()

    def _parse_item_ids(self, request: HttpRequest) -> list[int] | None:
        """Parse item_ids from POST body; return None if not provided."""
        return _parse_item_ids(request, where="ChangeSetApproveView._parse_item_ids")


class ChangeSetRejectView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/reject/  — reject pending operations.

    Body: item_ids (optional), reason (optional string).
    Creates a MuninRule if reason is provided.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST with optional item_ids and reason.
        :param changeset_id: ChangeSet PK.
        :return: HTMX partial with updated rows.
        """
        _story(
            "ChangeSetRejectView.post",
            "entry",
            user_pk=_user_pk(request),
            changeset_id=changeset_id,
        )
        try:
            item_ids = _parse_item_ids(request, where="ChangeSetRejectView.post")
        except ValueError:
            _story(
                "ChangeSetRejectView.post",
                "error",
                reason="bad_item_ids",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise
        _story(
            "ChangeSetRejectView.post",
            "branch",
            reason="all_items" if item_ids is None else "item_ids_filter",
            item_ids=item_ids,
        )
        raise NotImplementedError()


class ChangeSetDoOtherView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/do-other/  — redirect ops to Munin for re-planning.

    Body: item_ids (list[Any]), instructions (string).
    Queues Munin async re-plan; returns immediate response with task ID.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST with item_ids and instructions.
        :param changeset_id: ChangeSet PK.
        :return: HTMX partial confirming the re-plan was queued.
        """
        _story(
            "ChangeSetDoOtherView.post",
            "entry",
            user_pk=_user_pk(request),
            changeset_id=changeset_id,
        )
        try:
            item_ids = _parse_item_ids(request, where="ChangeSetDoOtherView.post")
        except ValueError:
            _story(
                "ChangeSetDoOtherView.post",
                "error",
                reason="bad_item_ids",
                changeset_id=changeset_id,
                level=logging.ERROR,
            )
            raise
        instructions = (request.POST.get("instructions") or "").strip()
        _story(
            "ChangeSetDoOtherView.post",
            "branch",
            reason="item_ids_filter" if item_ids else "all_items",
            item_ids=item_ids,
            has_instructions=bool(instructions),
        )
        if not item_ids or not instructions:
            _story(
                "ChangeSetDoOtherView.post",
                "error",
                reason="missing_fields",
                has_item_ids=bool(item_ids),
                has_instructions=bool(instructions),
                level=logging.ERROR,
            )
        raise NotImplementedError()


class ChangeSetRollbackView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/rollback/  — create rollback ChangeSet.

    Creates a new ChangeSet with source="rollback" reversing all applied ops.
    Returns HTMX redirect to the new rollback ChangeSet.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST (no body required).
        :param changeset_id: Applied ChangeSet to roll back. Example: 2
        :return: HTMX redirect to new rollback ChangeSet detail page.
        :raises Http404: If ChangeSet not found.
        :raises ValueError: If ChangeSet is not applied.
        """
        _story(
            "ChangeSetRollbackView.post",
            "entry",
            user_pk=_user_pk(request),
            changeset_id=changeset_id,
        )
        try:
            user = request.user
            rollback_user = user if user.is_authenticated else None
            rollback_cs = _service.rollback(changeset_id=changeset_id, user=rollback_user)
        except ValueError as exc:
            _story(
                "ChangeSetRollbackView.post",
                "error",
                reason="rollback_rejected",
                changeset_id=changeset_id,
                err=exc,
                level=logging.ERROR,
            )
            raise Http404(str(exc)) from exc
        redirect_url = reverse("changeset:detail", args=[rollback_cs.pk])
        response = HttpResponse(status=204)
        response["HX-Redirect"] = redirect_url
        _story(
            "ChangeSetRollbackView.post",
            "exit",
            status_code=204,
            rollback_id=rollback_cs.pk,
            hx_redirect=redirect_url,
        )
        return response
