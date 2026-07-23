"""Tests for MCP query tools (ACT-5-MCP-QUERY-01..11)."""

from __future__ import annotations

import pytest
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import (
    YggdrasilModelFactory,
)

from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.graph.models import ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset
from yggdrasil.mcp.tools.query import (
    get_changeset,
    get_element,
    list_changesets,
    list_elements,
    list_packages,
    list_stereotypes,
    search,
    traverse,
)


@pytest.fixture
def rw_user(db):
    user = UserFactory(username="query-tools", is_architect=True)
    set_current_user_id(user.pk)
    set_token_scope("read-write")
    yield user
    set_current_user_id(None)
    set_token_scope("read-write")


@pytest.fixture
def bootstrapped_model(rw_user):
    """Model with four manifest elements + relationships via Munin planner."""
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": name,
                "stereotype_slug": st,
                "package_slug": pkg,
            },
            "confidence": 0.95,
        }
        for name, st, pkg in [
            ("Payment API", "container", "technology"),
            ("Order Service", "container", "technology"),
            ("Order Domain", "component", "application"),
            ("Billing Worker", "component", "application"),
        ]
    ]
    propose_changeset(model="yggdrasil", operations=ops, run_id="run-query-fixture")
    return model


@pytest.mark.django_db
def test_list_elements_paginated(bootstrapped_model) -> None:
    """QUERY-01: list_elements returns manifest names."""
    result = list_elements(model="yggdrasil", limit=10, offset=0)
    names = {item["name"] for item in result["items"]}
    assert "Payment API" in names
    assert result["total"] >= 4


@pytest.mark.django_db
def test_search_by_name(bootstrapped_model) -> None:
    """QUERY-02: search finds Payment API."""
    result = search(query="Payment", model="yggdrasil")
    assert any(item["name"] == "Payment API" for item in result["items"])


@pytest.mark.django_db
def test_get_element_by_name(bootstrapped_model) -> None:
    """QUERY-03: get_element returns detail."""
    result = get_element(id_or_name="Payment API", model="yggdrasil")
    assert result["name"] == "Payment API"
    assert result["stereotype"]


@pytest.mark.django_db
def test_traverse_incoming_payment_api(bootstrapped_model) -> None:
    """QUERY-04: traverse incoming to Payment API."""
    result = traverse(from_="Payment API", direction="incoming", model="yggdrasil")
    assert result["source"]["name"] == "Payment API"
    assert len(result["edges"]) >= 1 or len(result["nodes"]) >= 1


@pytest.mark.django_db
def test_list_changesets(bootstrapped_model) -> None:
    """QUERY-07: list_changesets returns ratatosk source."""
    result = list_changesets(model="yggdrasil")
    assert result["total"] >= 1
    assert any(item.get("source") == "ratatosk" for item in result["items"])


@pytest.mark.django_db
def test_get_changeset(bootstrapped_model) -> None:
    """QUERY-08: get_changeset by id."""
    listed = list_changesets(model="yggdrasil")
    cs_id = listed["items"][0]["id"]
    detail = get_changeset(id=cs_id)
    assert detail["id"] == cs_id


@pytest.mark.django_db
def test_list_stereotypes(bootstrapped_model) -> None:
    """QUERY-09: list_stereotypes returns C4 catalog."""
    result = list_stereotypes(model="yggdrasil")
    slugs = {item["slug"] for item in result["items"]}
    assert "container" in slugs


@pytest.mark.django_db
def test_list_packages(bootstrapped_model) -> None:
    """QUERY-11: list_packages returns metamodel packages."""
    result = list_packages(model="yggdrasil")
    slugs = {item["slug"] for item in result["items"]}
    assert "technology" in slugs
    assert "application" in slugs
