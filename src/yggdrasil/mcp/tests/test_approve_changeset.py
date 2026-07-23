"""Tests for MCP approve_changeset (ACT-5-MCP-CHANGESET-01)."""

from __future__ import annotations

import pytest
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory

from yggdrasil.changeset.models import ChangeSet, ChangeSetItem
from yggdrasil.graph.models import Element, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.changeset import approve_changeset
from yggdrasil.mcp.tools.propose import propose_changeset


@pytest.fixture
def rw_user(db):
    user = UserFactory(username="approve-cs", is_architect=True)
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    yield user
    set_current_user_id(None)
    set_token_scope("read-write")


@pytest.mark.django_db
def test_approve_changeset_applies_pending_items(rw_user) -> None:
    """CHANGESET-01: manual approve applies sub-threshold ops."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = propose_changeset(
        model="yggdrasil",
        operations=[
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": "Low Conf Service",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.5,
            }
        ],
        confidence_threshold=0.80,
        run_id="run-low",
    )
    assert result["pending_count"] == 1
    cs = ChangeSet.objects.get(pk=result["changeset_id"])
    pending_ids = list(
        cs.items.filter(status=ChangeSetItem.ITEM_STATUS_PENDING).values_list("pk", flat=True)
    )
    approved = approve_changeset(id=cs.pk, item_ids=pending_ids)
    assert approved["applied_count"] == 1
    assert Element.objects.filter(name="Low Conf Service").exists()


@pytest.mark.django_db
def test_approve_changeset_rejects_readonly(rw_user) -> None:
    """Read-only token cannot approve."""
    ensure_c4_metamodel()
    YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=ensure_c4_metamodel())
    result = propose_changeset(
        model="yggdrasil",
        operations=[
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": "Pending",
                    "stereotype_slug": "container",
                    "package_slug": "technology",
                },
                "confidence": 0.5,
            }
        ],
        confidence_threshold=0.80,
        run_id="run-ro-approve",
    )
    set_token_scope("read-only")
    with pytest.raises(PermissionError):
        approve_changeset(id=result["changeset_id"])
