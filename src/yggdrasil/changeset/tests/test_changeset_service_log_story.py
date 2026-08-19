"""Log story tests for ChangeSetService and changeset views."""

from __future__ import annotations

import logging

import pytest
from django.test import RequestFactory
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.support.log_story import assert_log_story

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.changeset.services import ChangeSetService
from yggdrasil.changeset.views import (
    ChangeSetApproveView,
    ChangeSetListView,
    ChangeSetRollbackView,
)
from yggdrasil.graph.models import ensure_c4_metamodel

LOGGER = "yggdrasil.changeset"


def _add_element_op(name: str, confidence: float = 0.9) -> dict:
    return {
        "op_type": ChangeSetItem.OP_ADD_ELEMENT,
        "detail": {
            "name": name,
            "stereotype_slug": "container",
            "package_slug": "technology",
        },
        "confidence": confidence,
    }


def _add_relationship_op(**detail: object) -> dict:
    payload = {"stereotype_slug": "depends_on", **detail}
    return {
        "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
        "detail": payload,
        "confidence": 0.9,
    }


@pytest.fixture
def svc() -> ChangeSetService:
    return ChangeSetService()


@pytest.fixture
def ymodel(db):
    metamodel = ensure_c4_metamodel()
    return YggdrasilModelFactory(
        name="CS Log Model",
        slug="cs-log-model",
        metamodel=metamodel,
    )


@pytest.fixture
def user(db):
    return UserFactory(username="cs-log-user", is_architect=True)


@pytest.mark.django_db
def test_propose_log_story_reject_empty_ops(caplog, svc, ymodel, user) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="empty"),
    ):
        svc.propose(model_id=ymodel.pk, source="mcp", operations=[], user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService.propose",
        beats={
            "entry": [
                "model_id=",
                "source=",
                "ops=",
                "user_id=",
                "allow_empty=",
            ],
            "validation": ["ops=0"],
            "error": ["reason=empty_operations"],
        },
    )


@pytest.mark.django_db
def test_propose_log_story_reject_invalid_source(caplog, svc, ymodel) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="Invalid source"),
    ):
        svc.propose(
            model_id=ymodel.pk,
            source="not-a-source",
            operations=[_add_element_op("X")],
        )
    assert_log_story(
        caplog,
        where="ChangeSetService.propose",
        beats={"error": ["reason=invalid_source", "source=not-a-source"]},
    )


@pytest.mark.django_db
def test_propose_log_story_reject_model_not_found(caplog, svc) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="not found"),
    ):
        svc.propose(
            model_id=999_999,
            source="mcp",
            operations=[_add_element_op("Ghost")],
        )
    assert_log_story(
        caplog,
        where="ChangeSetService.propose",
        beats={"error": ["reason=model_not_found", "model_id=999999"]},
    )


@pytest.mark.django_db
def test_propose_log_story_happy(caplog, svc, ymodel, user) -> None:
    ops = [
        _add_element_op("Payment API"),
        _add_relationship_op(source_name="A", target_name="B"),
    ]
    with caplog.at_level(logging.INFO, logger=LOGGER):
        changeset = svc.propose(
            model_id=ymodel.pk,
            source="mcp",
            operations=ops,
            user=user,
        )
    assert_log_story(
        caplog,
        where="ChangeSetService.propose",
        beats={
            "entry": [
                f"model_id={ymodel.pk}",
                "source=mcp",
                "ops=2",
                f"user_id={user.pk}",
                "allow_empty=False",
            ],
            "processing": ["add_element=1", "add_relationship=1"],
            "exit": [
                f"changeset_id={changeset.pk}",
                "status=pending",
                "item_count=2",
            ],
        },
    )


@pytest.mark.django_db
def test_approve_log_story_happy(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Low Conf Service")],
        user=user,
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        applied = svc.approve(changeset_id=changeset.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService.approve",
        beats={
            "entry": [f"changeset_id={changeset.pk}", "item_ids=None", f"user={user.pk}"],
            "processing": ["selected_count=1"],
            "exit": ["status=applied", "applied_count=1"],
        },
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._apply_item",
        beats={"processing": ["item=", "op=add_element", f"changeset={changeset.pk}"]},
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._apply_add_element",
        beats={
            "processing": ["created="],
            "branch": ["reason=created"],
        },
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._finalize_changeset_status",
        beats={"branch": ["reason=applied", "accepted=1"]},
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._select_pending_items",
        beats={"branch": ["reason=all_pending"]},
    )
    assert applied.status == ChangeSet.STATUS_APPLIED


@pytest.mark.django_db
def test_approve_log_story_reject_already_applied(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Once")],
        user=user,
    )
    svc.approve(changeset_id=changeset.pk, user=user)
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="already applied"),
    ):
        svc.approve(changeset_id=changeset.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._get_pending_changeset",
        beats={"error": ["reason=already_applied", f"changeset_id={changeset.pk}"]},
    )


@pytest.mark.django_db
def test_approve_log_story_reject_not_found(caplog, svc) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="not found"),
    ):
        svc.approve(changeset_id=888_888)
    assert_log_story(
        caplog,
        where="ChangeSetService._get_pending_changeset",
        beats={"error": ["reason=not_found", "changeset_id=888888"]},
    )


@pytest.mark.django_db
def test_select_pending_items_log_story_missing_ids(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Keep")],
        user=user,
    )
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="Pending items not found"),
    ):
        svc.approve(changeset_id=changeset.pk, item_ids=[999_001], user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._select_pending_items",
        beats={"error": ["reason=missing_ids", "999001"]},
    )


@pytest.mark.django_db
def test_finalize_still_pending_log_story(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("One"), _add_element_op("Two")],
        user=user,
    )
    first_id = changeset.items.order_by("order").first().pk
    with caplog.at_level(logging.INFO, logger=LOGGER):
        svc.approve(changeset_id=changeset.pk, item_ids=[first_id], user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._select_pending_items",
        beats={"branch": ["reason=item_ids_filter", "selected_count=1"]},
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._finalize_changeset_status",
        beats={"branch": ["reason=still_pending", "remaining=1"]},
    )


@pytest.mark.django_db
def test_reject_log_story_learn_rule(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Skip Me")],
        user=user,
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        rejected = svc.reject(
            changeset_id=changeset.pk,
            reason="Not a runtime service",
            user=user,
            learn=True,
        )
    assert_log_story(
        caplog,
        where="ChangeSetService.reject",
        beats={
            "entry": [f"changeset_id={changeset.pk}", "learn=True", f"user={user.pk}"],
            "branch": ["reason=learn_rule"],
            "exit": ["rejected_count=1", f"status={rejected.status}"],
        },
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._finalize_changeset_status",
        beats={"branch": ["reason=rejected", "rejected=1"]},
    )


@pytest.mark.django_db
def test_reject_log_story_no_rule(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("No Learn")],
        user=user,
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        svc.reject(changeset_id=changeset.pk, reason="", user=user, learn=False)
    assert_log_story(
        caplog,
        where="ChangeSetService.reject",
        beats={"branch": ["reason=no_rule", "learn=False"]},
    )


@pytest.mark.django_db
def test_do_other_log_story_reject_empty_item_ids(caplog, svc) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="item_id"),
    ):
        svc.do_other(changeset_id=1, item_ids=[], instructions="replan this")
    assert_log_story(
        caplog,
        where="ChangeSetService.do_other",
        beats={
            "entry": ["changeset_id=1", "item_ids=[]"],
            "validation": ["item_ids_count=0"],
            "error": ["reason=empty_item_ids"],
        },
    )


@pytest.mark.django_db
def test_do_other_log_story_reject_empty_instructions(caplog, svc) -> None:
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="instructions"),
    ):
        svc.do_other(changeset_id=1, item_ids=[1], instructions="   ")
    assert_log_story(
        caplog,
        where="ChangeSetService.do_other",
        beats={"error": ["reason=empty_instructions"]},
    )


@pytest.mark.django_db
def test_do_other_log_story_happy(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Replan Me")],
        user=user,
    )
    item_id = changeset.items.get().pk
    with caplog.at_level(logging.INFO, logger=LOGGER):
        result = svc.do_other(
            changeset_id=changeset.pk,
            item_ids=[item_id],
            instructions="treat as external system",
            user=user,
        )
    replacements = getattr(result, "_do_other_replacements", [])
    assert replacements
    assert_log_story(
        caplog,
        where="ChangeSetService.do_other",
        beats={
            "processing": ["replacement_ids="],
            "exit": [f"changeset_id={changeset.pk}", "redirected=1"],
        },
    )


@pytest.mark.django_db
def test_rollback_log_story_not_applied(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Pending Only")],
        user=user,
    )
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="rollback requires"),
    ):
        svc.rollback(changeset_id=changeset.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService.rollback",
        beats={
            "entry": [f"changeset_id={changeset.pk}"],
            "validation": ["reason=not_applied", f"status={ChangeSet.STATUS_PENDING}"],
        },
    )


@pytest.mark.django_db
def test_rollback_log_story_happy(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("To Reverse")],
        user=user,
    )
    svc.approve(changeset_id=changeset.pk, user=user)
    with caplog.at_level(logging.INFO, logger=LOGGER):
        rollback_cs = svc.rollback(changeset_id=changeset.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService.rollback",
        beats={
            "processing": ["delete_element=1"],
            "exit": [f"rollback_id={rollback_cs.pk}"],
        },
    )


@pytest.mark.django_db
def test_apply_add_element_existing_log_story(caplog, svc, ymodel, user) -> None:
    first = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Shared Name")],
        user=user,
    )
    svc.approve(changeset_id=first.pk, user=user)
    second = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("Shared Name")],
        user=user,
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        svc.approve(changeset_id=second.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._apply_add_element",
        beats={"branch": ["reason=existing_element"], "processing": ["created=False"]},
    )


@pytest.mark.django_db
def test_resolve_element_id_log_story_by_slug_and_name(caplog, svc, ymodel, user) -> None:
    svc.approve(
        changeset_id=svc.propose(
            model_id=ymodel.pk,
            source="mcp",
            operations=[_add_element_op("Alpha Svc"), _add_element_op("Beta Svc")],
            user=user,
        ).pk,
        user=user,
    )
    by_slug = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[
            _add_relationship_op(source_slug="alpha-svc", target_slug="beta-svc"),
        ],
        user=user,
    )
    with caplog.at_level(logging.INFO, logger=LOGGER):
        svc.approve(changeset_id=by_slug.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._resolve_element_id",
        beats={"branch": ["reason=by_slug", "slug=alpha-svc"]},
    )
    assert_log_story(
        caplog,
        where="ChangeSetService._apply_add_relationship",
        beats={"processing": ["source_id=", "target_id=", "stereotype=depends_on"]},
    )

    by_name = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[
            _add_relationship_op(source_name="Alpha Svc", target_name="Beta Svc"),
        ],
        user=user,
    )
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=LOGGER):
        svc.approve(changeset_id=by_name.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._resolve_element_id",
        beats={"branch": ["reason=by_name", "name=Alpha Svc"]},
    )


@pytest.mark.django_db
def test_resolve_element_id_log_story_not_found(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_relationship_op(source_name="Missing", target_name="Gone")],
        user=user,
    )
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="Element not found"),
    ):
        svc.approve(changeset_id=changeset.pk, user=user)
    assert_log_story(
        caplog,
        where="ChangeSetService._resolve_element_id",
        beats={"error": ["reason=not_found", "name=Missing"]},
    )


@pytest.mark.django_db
def test_list_view_log_story_entry_and_filter_branch(caplog, user) -> None:
    factory = RequestFactory()
    request = factory.get("/changesets/", {"status": "pending"})
    request.user = user
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(NotImplementedError),
    ):
        ChangeSetListView().get(request)
    assert_log_story(
        caplog,
        where="ChangeSetListView.get",
        beats={
            "entry": [f"user_pk={user.pk}"],
            "branch": ["reason=status_filter", "status=pending"],
        },
    )


@pytest.mark.django_db
def test_approve_view_log_story_bad_item_ids(caplog, user) -> None:
    factory = RequestFactory()
    request = factory.post("/changesets/1/approve/", {"item_ids": "nope"})
    request.user = user
    with (
        caplog.at_level(logging.INFO, logger=LOGGER),
        pytest.raises(ValueError, match="invalid item_ids"),
    ):
        ChangeSetApproveView().post(request, changeset_id=1)
    assert_log_story(
        caplog,
        where="ChangeSetApproveView.post",
        beats={
            "entry": [f"user_pk={user.pk}", "changeset_id=1"],
            "error": ["reason=bad_item_ids"],
        },
    )


@pytest.mark.django_db
def test_rollback_view_log_story_exit(caplog, svc, ymodel, user) -> None:
    changeset = svc.propose(
        model_id=ymodel.pk,
        source="mcp",
        operations=[_add_element_op("View Rollback")],
        user=user,
    )
    svc.approve(changeset_id=changeset.pk, user=user)
    factory = RequestFactory()
    request = factory.post(f"/changesets/{changeset.pk}/rollback/")
    request.user = user
    with caplog.at_level(logging.INFO, logger=LOGGER):
        response = ChangeSetRollbackView().post(request, changeset_id=changeset.pk)
    assert response.status_code == 204
    assert_log_story(
        caplog,
        where="ChangeSetRollbackView.post",
        beats={
            "entry": [f"user_pk={user.pk}", f"changeset_id={changeset.pk}"],
            "exit": ["status_code=204", "hx_redirect="],
        },
    )
