"""Shared View Browser test fixtures — six mock-aligned elements."""

from __future__ import annotations

import pytest

from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.graph.models import Element, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset

VIEW_BROWSER_ELEMENTS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("Payment API", "container", "technology", "payments-team", "green", "ratatosk"),
    ("Notification Service", "container", "technology", "platform-team", "yellow", "human"),
    ("Order Domain", "component", "application", "fulfillment-team", "green", "ratatosk"),
    ("Fulfillment Worker", "component", "application", "fulfillment-team", "red", "ratatosk"),
    ("PostgreSQL", "system", "technology", "platform-team", "green", "ratatosk"),
    ("Mobile App", "system", "context", "mobile-team", "green", "ratatosk"),
)


@pytest.fixture
def view_browser_user(db):
    """Architect user for View Browser web tests."""
    return UserFactory(username="view-browser-architect", is_architect=True)


@pytest.fixture
def view_browser_model(db, view_browser_user):
    """
    Model with six elements aligned to VIEW-BROWSE-1 mock names.

    Also seeds relationships among technology elements for graph tests.
    """
    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": name,
                "stereotype_slug": st,
                "package_slug": pkg,
                "owner": owner,
            },
            "confidence": 0.95,
        }
        for name, st, pkg, owner, _health, _source in VIEW_BROWSER_ELEMENTS
    ]
    ops.extend(
        [
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": "Mobile App",
                    "target_name": "Payment API",
                    "stereotype_slug": "calls",
                },
                "confidence": 0.9,
            },
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": "Payment API",
                    "target_name": "PostgreSQL",
                    "stereotype_slug": "depends_on",
                },
                "confidence": 0.99,
            },
        ]
    )
    propose_changeset(model="yggdrasil", operations=ops, run_id="run-view-browser-fixture")
    for name, _st, _pkg, _owner, health, source in VIEW_BROWSER_ELEMENTS:
        Element.objects.filter(model=model, name=name).update(health=health, source=source)
    yield model
    set_current_user_id(None)
    set_token_scope("read-write")
