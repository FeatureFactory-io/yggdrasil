"""
Common AT step helpers and wait steps.

Steps:
  - When the user waits {seconds:d} seconds
  - Given ChangeSet id={cs_id:d} is applied with {count:d} accepted operations
  - When/Given Marcus clicks [Roll Back Entire Run]
  - Then a new ChangeSet is created with source "rollback"
  - Then the rollback ChangeSet reverses all {count:d} operations from ChangeSet id={cs_id:d}
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from behave import given, then, when
from django.utils import timezone

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import YggdrasilModel, ensure_c4_metamodel

if TYPE_CHECKING:
    from django.test import Client

logger = logging.getLogger(__name__)

_INVERSE_OP_TYPES = {
    ChangeSetItem.OP_ADD_ELEMENT: ChangeSetItem.OP_DELETE_ELEMENT,
    ChangeSetItem.OP_DELETE_ELEMENT: ChangeSetItem.OP_ADD_ELEMENT,
    ChangeSetItem.OP_ADD_RELATIONSHIP: ChangeSetItem.OP_DELETE_RELATIONSHIP,
    ChangeSetItem.OP_DELETE_RELATIONSHIP: ChangeSetItem.OP_ADD_RELATIONSHIP,
    ChangeSetItem.OP_UPDATE_ELEMENT: ChangeSetItem.OP_UPDATE_ELEMENT,
    ChangeSetItem.OP_ADD_TO_DIAGRAM: ChangeSetItem.OP_ADD_TO_DIAGRAM,
}


def get_client(context) -> Client:
    """Return the Django test client attached by behave-django."""
    return context.test.client


def get_response_content(context) -> str:
    """Decode the last HTTP response body as text."""
    if not hasattr(context, "response"):
        msg = "No HTTP response on context — call a When step that performs a request first."
        raise AssertionError(msg)
    return context.response.content.decode()


@when("the user waits {seconds:d} seconds")
def step_user_waits(context, seconds: int) -> None:
    """Pause execution (AT harness — rarely needed without a browser)."""
    logger.info("Waiting %s seconds", seconds)
    time.sleep(seconds)


# ─── ChangeSet state setup steps (Group B — S33) ────────────────────────────


@given("ChangeSet id={cs_id:d} is applied with {count:d} accepted operations")
def step_applied_changeset(context, cs_id: int, count: int) -> None:
    """Create an applied ChangeSet with N accepted ChangeSetItems in the test DB."""
    model = _ensure_default_model()
    changeset = ChangeSet(
        pk=cs_id,
        model=model,
        source=ChangeSet.SOURCE_RATATOSK,
        status=ChangeSet.STATUS_APPLIED,
        review_mode=ChangeSet.REVIEW_AUTO,
        run_id=f"run-{cs_id:03d}",
        munin_reasoning="Applied ChangeSet for rollback AT",
        applied_at=timezone.now(),
    )
    changeset.save()
    ChangeSetItem.objects.filter(changeset=changeset).delete()
    for order in range(1, count + 1):
        ChangeSetItem.objects.create(
            changeset=changeset,
            order=order,
            op_type=ChangeSetItem.OP_ADD_ELEMENT,
            detail={
                "name": f"Element {order}",
                "stereotype_slug": "container",
                "element_id": 100 + order,
            },
            status=ChangeSetItem.ITEM_STATUS_ACCEPTED,
            confidence=0.9,
        )
    context.changeset_id = cs_id
    context.applied_changeset = changeset
    logger.info(
        "step_applied_changeset | changeset_id=%s accepted_ops=%s",
        cs_id,
        count,
    )


@given("Marcus clicks [Roll Back Entire Run]")
def step_marcus_clicks_rollback(context) -> None:
    """POST to /changesets/<id>/rollback/ via the test client."""
    _post_rollback(context)


@when("Marcus clicks [Roll Back Entire Run]")
def step_marcus_clicks_rollback_btn(context) -> None:
    """POST to the rollback endpoint for the current ChangeSet in context."""
    _post_rollback(context)


@then('a new ChangeSet is created with source "rollback"')
def step_rollback_changeset_created(context) -> None:
    """Assert a new rollback ChangeSet was created in the DB."""
    rollback_cs = (
        ChangeSet.objects.filter(source=ChangeSet.SOURCE_ROLLBACK).order_by("-created_at").first()
    )
    assert rollback_cs is not None, "Expected a ChangeSet with source='rollback'"
    context.rollback_changeset = rollback_cs
    logger.info(
        "step_rollback_changeset_created | rollback_id=%s",
        rollback_cs.pk,
    )


@then("the rollback ChangeSet reverses all {count:d} operations from ChangeSet id={cs_id:d}")
def step_rollback_reverses_ops(context, count: int, cs_id: int) -> None:
    """Assert the rollback ChangeSet contains N inverse operations."""
    rollback_cs = getattr(context, "rollback_changeset", None)
    if rollback_cs is None:
        rollback_cs = (
            ChangeSet.objects.filter(source=ChangeSet.SOURCE_ROLLBACK)
            .order_by("-created_at")
            .first()
        )
    assert rollback_cs is not None, "No rollback ChangeSet on context or in DB"
    items = list(rollback_cs.items.all())
    assert len(items) == count, f"Expected {count} rollback ops, got {len(items)}"

    source_items = list(
        ChangeSetItem.objects.filter(
            changeset_id=cs_id,
            status=ChangeSetItem.ITEM_STATUS_ACCEPTED,
        ).order_by("order")
    )
    assert (
        len(source_items) == count
    ), f"Source ChangeSet id={cs_id} has {len(source_items)} accepted ops, expected {count}"

    # Rollback items are created in reverse apply order.
    expected_pairs = list(reversed(source_items))
    for rollback_item, source_item in zip(items, expected_pairs, strict=True):
        expected_op = _INVERSE_OP_TYPES[source_item.op_type]
        assert rollback_item.op_type == expected_op, (
            f"Expected inverse {expected_op!r} for {source_item.op_type!r}, "
            f"got {rollback_item.op_type!r}"
        )
    logger.info(
        "step_rollback_reverses_ops | rollback_id=%s count=%s source_id=%s",
        rollback_cs.pk,
        count,
        cs_id,
    )


def _post_rollback(context) -> None:
    """POST rollback for context.changeset_id and store response."""
    cs_id = getattr(context, "changeset_id", None)
    assert cs_id is not None, "context.changeset_id missing — run the Given applied step first"
    client = get_client(context)
    url = f"/changesets/{cs_id}/rollback/"
    logger.info("_post_rollback | POST %s user=%s", url, getattr(context, "current_user", None))
    context.response = client.post(url)
    assert context.response.status_code in {
        200,
        204,
        302,
    }, f"Rollback POST {url} returned {context.response.status_code}"
    # Keep a service-level handle for assertions if HTMX body is empty.
    if not hasattr(context, "rollback_changeset"):
        context.rollback_changeset = (
            ChangeSet.objects.filter(source=ChangeSet.SOURCE_ROLLBACK)
            .order_by("-created_at")
            .first()
        )


def _ensure_default_model() -> YggdrasilModel:
    """Return (or create) the default Yggdrasil model used by AT fixtures."""
    model, created = YggdrasilModel.objects.get_or_create(
        slug="yggdrasil",
        defaults={"name": "Yggdrasil", "metamodel": ensure_c4_metamodel()},
    )
    logger.info("_ensure_default_model | model_id=%s created=%s", model.pk, created)
    return model
