"""
ChangeSet views: list, detail, approve/reject/do-other/rollback actions.

All mutating actions delegate to ChangeSetService (SAO.md §3 — layer separation).
Views never call ORM directly.

Screen IDs (docs/ux/2_dialogue-maps/screen-flow.md):
  CHANGESET-LIST+FIND-1  → ChangeSetListView (GET /changesets/)
  CHANGESET-VIEW_CHANGESET-1 → ChangeSetDetailView (GET /changesets/<id>/)

HTMX partials returned for approve/reject/do-other/rollback actions.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View

from yggdrasil.changeset.services import ChangeSetService

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("yggdrasil.changeset")

_service = ChangeSetService()


class ChangeSetListView(LoginRequiredMixin, View):
    """
    GET /changesets/  — list all ChangeSets with status/source filters.

    Query params: ?status=pending|applied|rejected, ?source=ratatosk|human|mcp
    :Example: GET /changesets/?status=pending → 200 with filtered list
    """

    template_name = "changeset/list.html"

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        :param request: GET request with optional ?status and ?source params.
        :return: 200 rendered list page.
        """
        raise NotImplementedError()

    def _get_filter_params(self, request: HttpRequest) -> dict:
        """Extract and validate status/source query parameters."""
        raise NotImplementedError()


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
        raise NotImplementedError()


class ChangeSetApproveView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/approve/  — apply pending operations.

    Body: item_ids (optional JSON list) — omit to approve all.
    Returns HTMX partial updating the operation rows.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST with optional item_ids JSON body.
        :param changeset_id: ChangeSet PK.
        :return: HTMX partial with updated operation rows.
        :raises Http404: If ChangeSet not found.
        """
        raise NotImplementedError()

    def _parse_item_ids(self, request: HttpRequest) -> list[int] | None:
        """Parse item_ids from POST body; return None if not provided."""
        raise NotImplementedError()


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
        raise NotImplementedError()


class ChangeSetDoOtherView(LoginRequiredMixin, View):
    """
    POST /changesets/<id>/do-other/  — redirect ops to Munin for re-planning.

    Body: item_ids (list), instructions (string).
    Queues Munin async re-plan; returns immediate response with task ID.
    """

    def post(self, request: HttpRequest, changeset_id: int) -> HttpResponse:
        """
        :param request: POST with item_ids and instructions.
        :param changeset_id: ChangeSet PK.
        :return: HTMX partial confirming the re-plan was queued.
        """
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
        raise NotImplementedError()
