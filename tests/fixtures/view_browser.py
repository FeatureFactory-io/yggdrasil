"""Shared View Browser test fixtures — payment (6) and explorer (19) models."""

from __future__ import annotations

import pytest

from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from yggdrasil.changeset.models import ChangeSetItem
from yggdrasil.graph.models import Element, ensure_c4_metamodel
from yggdrasil.mcp.server import set_current_user_id, set_token_scope
from yggdrasil.mcp.tools.propose import propose_changeset

# Tuple: name, stereotype_slug, package_slug, owner, health, source [, element_slug]
ElementSpec = tuple[str, str, str, str, str, str] | tuple[str, str, str, str, str, str, str]
RelationshipSpec = tuple[str, str, str, float]

VIEW_BROWSER_ELEMENTS: tuple[ElementSpec, ...] = (
    ("Payment API", "container", "technology", "payments-team", "green", "ratatosk"),
    ("Notification Service", "container", "technology", "platform-team", "yellow", "human"),
    ("Order Domain", "component", "application", "fulfillment-team", "green", "ratatosk"),
    ("Fulfillment Worker", "component", "application", "fulfillment-team", "red", "ratatosk"),
    ("PostgreSQL", "system", "technology", "platform-team", "green", "ratatosk"),
    ("Mobile App", "system", "context", "mobile-team", "green", "ratatosk"),
)

VIEW_BROWSER_EXPLORER_ELEMENTS: tuple[tuple[str, str, str, str, str, str, str], ...] = (
    ("Yggdrasil", "system", "context", "platform-team", "green", "ratatosk", "yggdrasil"),
    ("Browser (HTMX)", "person", "context", "", "green", "ratatosk", "browser-htmx"),
    ("AI agents", "person", "context", "", "green", "ratatosk", "ai-agents"),
    (
        "Backend (web + Celery)",
        "container",
        "application",
        "platform-team",
        "green",
        "ratatosk",
        "backend-web-celery",
    ),
    ("MCP facade", "container", "application", "platform-team", "green", "ratatosk", "mcp-facade"),
    (
        "Ratatosk CLI",
        "container",
        "application",
        "platform-team",
        "green",
        "ratatosk",
        "ratatosk-cli",
    ),
    ("Worker", "container", "application", "platform-team", "green", "ratatosk", "worker"),
    ("auth", "component", "application", "platform-team", "green", "ratatosk", "auth"),
    ("graph", "component", "application", "platform-team", "green", "ratatosk", "graph"),
    ("changeset", "component", "application", "platform-team", "green", "ratatosk", "changeset"),
    ("munin", "component", "application", "platform-team", "green", "ratatosk", "munin"),
    ("ratatosk", "component", "application", "platform-team", "green", "ratatosk", "ratatosk"),
    ("mcp", "component", "application", "platform-team", "green", "ratatosk", "mcp"),
    ("api", "component", "application", "platform-team", "green", "ratatosk", "api"),
    ("web", "component", "application", "platform-team", "green", "ratatosk", "web"),
    ("llm", "component", "application", "platform-team", "green", "ratatosk", "llm"),
    ("PostgreSQL", "container", "technology", "platform-team", "green", "ratatosk", "postgre-sql"),
    ("Redis", "container", "technology", "platform-team", "green", "ratatosk", "redis"),
    ("Ollama", "container", "technology", "platform-team", "green", "ratatosk", "ollama"),
)

VIEW_BROWSER_EXPLORER_RELATIONSHIPS: tuple[RelationshipSpec, ...] = (
    ("Browser (HTMX)", "Backend (web + Celery)", "uses", 0.9),
    ("MCP facade", "Backend (web + Celery)", "calls", 0.95),
    ("Ratatosk CLI", "MCP facade", "calls", 0.9),
    ("AI agents", "MCP facade", "uses", 0.85),
    ("auth", "Backend (web + Celery)", "depends_on", 0.9),
    ("graph", "Backend (web + Celery)", "depends_on", 0.9),
    ("munin", "Backend (web + Celery)", "depends_on", 0.9),
    ("munin", "llm", "depends_on", 0.88),
    ("changeset", "graph", "depends_on", 0.92),
    ("Backend (web + Celery)", "Redis", "depends_on", 0.95),
    ("llm", "Ollama", "depends_on", 0.85),
)

_PAYMENT_RELATIONSHIPS: tuple[RelationshipSpec, ...] = (
    ("Mobile App", "Payment API", "calls", 0.9),
    ("Payment API", "PostgreSQL", "depends_on", 0.99),
)


def _seed_view_browser(
    model,
    element_specs: tuple[ElementSpec, ...],
    relationship_specs: tuple[RelationshipSpec, ...],
    *,
    run_id: str,
) -> None:
    """
    Seed a model with elements and relationships via the ChangeSet pipeline.

    :param model: Target ``YggdrasilModel`` instance.
    :param element_specs: Rows of (name, stereotype, package, owner, health, source [, slug]).
    :param relationship_specs: Rows of (source_name, target_name, stereotype_slug, confidence).
    :param run_id: Ratatosk run id for audit trail.
    """
    ops: list[dict] = []
    slug_overrides: dict[str, str] = {}
    health_source: list[tuple[str, str, str]] = []

    for row in element_specs:
        name, stereotype, package, owner = row[0], row[1], row[2], row[3]
        health, source = row[4], row[5]
        if len(row) == 7:
            slug_overrides[name] = row[6]
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_ELEMENT,
                "detail": {
                    "name": name,
                    "stereotype_slug": stereotype,
                    "package_slug": package,
                    "owner": owner,
                },
                "confidence": 0.95,
            }
        )
        health_source.append((name, health, source))

    for source_name, target_name, edge_st, confidence in relationship_specs:
        ops.append(
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": source_name,
                    "target_name": target_name,
                    "stereotype_slug": edge_st,
                },
                "confidence": confidence,
            }
        )

    propose_changeset(model=model.slug, operations=ops, run_id=run_id)

    for name, health, source in health_source:
        Element.objects.filter(model=model, name=name).update(health=health, source=source)

    for name, slug in slug_overrides.items():
        Element.objects.filter(model=model, name=name).update(slug=slug)


@pytest.fixture
def view_browser_user(db):
    """Architect user for View Browser web tests."""
    from django.contrib.auth.models import Group

    user = UserFactory(username="view-browser-architect", is_architect=True)
    architect_group, _ = Group.objects.get_or_create(name="architect")
    user.groups.add(architect_group)
    return user


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
    _seed_view_browser(
        model,
        VIEW_BROWSER_ELEMENTS,
        _PAYMENT_RELATIONSHIPS,
        run_id="run-view-browser-fixture",
    )
    yield model
    set_current_user_id(None)
    set_token_scope("read-write")


@pytest.fixture
def view_browser_explorer_model(db, view_browser_user):
    """Yggdrasil self-model with 19 elements and 11 relationships for v0.3 navigator tests."""
    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil", metamodel=mm)
    _seed_view_browser(
        model,
        VIEW_BROWSER_EXPLORER_ELEMENTS,
        VIEW_BROWSER_EXPLORER_RELATIONSHIPS,
        run_id="run-view-browser-explorer-fixture",
    )
    yield model
    set_current_user_id(None)
    set_token_scope("read-write")
