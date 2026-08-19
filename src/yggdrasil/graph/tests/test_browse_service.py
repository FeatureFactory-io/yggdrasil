"""Tests for graph browse_service (Act 2 View Browser foundation)."""

from __future__ import annotations

import logging

import pytest
from django.contrib.auth.models import Group
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_service
from yggdrasil.graph.models import Element
from yggdrasil.mcp.tools.query import list_elements as mcp_list_elements


@pytest.mark.django_db
def test_list_readable_models_all_when_owner_group_null() -> None:
    """W12: user sees Models with null owner_group."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Beta", slug="beta")
    slugs = {model.slug for model in browse_service.list_readable_models(user)}
    assert slugs == {"alpha", "beta"}


@pytest.mark.django_db
def test_list_readable_models_filters_by_owner_group() -> None:
    """W12: user only sees Models owned by their group."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Shared", slug="shared", owner_group=architect_group)
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    slugs = {model.slug for model in browse_service.list_readable_models(user)}
    assert slugs == {"shared"}


@pytest.mark.django_db
def test_list_readable_models_superuser_sees_all() -> None:
    """W12: admin bypass sees every Model."""
    architect_group, _ = Group.objects.get_or_create(name="architect")
    admin = UserFactory(is_admin=True)
    YggdrasilModelFactory(name="Locked", slug="locked", owner_group=architect_group)
    slugs = {model.slug for model in browse_service.list_readable_models(admin)}
    assert "locked" in slugs


@pytest.mark.django_db
def test_resolve_default_model_sole_visible() -> None:
    """W12: exactly one readable Model becomes the default."""
    user = UserFactory()
    YggdrasilModelFactory(name="Only", slug="only")
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) == "only"


@pytest.mark.django_db
def test_resolve_default_model_cookie_preference() -> None:
    """W12: valid cookie wins over name ordering."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Zulu", slug="zulu")
    assert browse_service.resolve_default_model_slug(user, cookie_value="zulu") == "zulu"


@pytest.mark.django_db
def test_resolve_default_model_first_by_name() -> None:
    """W12: fallback is first readable Model by name."""
    user = UserFactory()
    YggdrasilModelFactory(name="Beta", slug="beta")
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) == "alpha"


@pytest.mark.django_db
def test_resolve_default_model_no_readable_returns_none() -> None:
    """W12: zero readable Models yields None."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    assert browse_service.resolve_default_model_slug(user, cookie_value=None) is None


@pytest.mark.django_db
def test_user_can_read_model_rejects_private() -> None:
    """W12: unreadable slug raises PermissionError."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    with pytest.raises(PermissionError):
        browse_service.user_can_read_model(user, "private")


@pytest.mark.django_db
def test_list_readable_models_log_story_happy(caplog) -> None:
    """Readable-model query logs ACL branch, not only entry/exit counts."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.list_readable_models(user)
    assert_log_story(
        caplog,
        where="browse_service.list_readable_models",
        beats={
            "entry": ["user_pk="],
            "branch": ["reason=group_acl", "group_ids="],
            "exit": ["model_count="],
        },
    )


@pytest.mark.django_db
def test_user_can_read_model_log_story_reject(caplog) -> None:
    """Denied Model access logs why, not a silent PermissionError."""
    other_group, _ = Group.objects.get_or_create(name="other-team")
    user = UserFactory(groups="architect")
    YggdrasilModelFactory(name="Private", slug="private", owner_group=other_group)
    with (
        caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"),
        pytest.raises(PermissionError),
    ):
        browse_service.user_can_read_model(user, "private")
    assert_log_story(
        caplog,
        where="browse_service.user_can_read_model",
        beats={
            "entry": ["user_pk=", "model_slug=private"],
            "error": ["reason=not_readable", "readable_count="],
        },
    )


@pytest.mark.django_db
def test_resolve_default_model_log_story_happy(caplog) -> None:
    """W12: default resolver emits branch beats."""
    user = UserFactory()
    YggdrasilModelFactory(name="Alpha", slug="alpha")
    YggdrasilModelFactory(name="Beta", slug="beta")
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.resolve_default_model_slug(user, cookie_value="beta")
    assert_log_story(
        caplog,
        where="browse_service.resolve_default_model_slug",
        beats={
            "entry": ["user_pk="],
            "cookie": ["reason=cookie", "model_slug=beta"],
        },
    )


@pytest.mark.django_db
def test_list_elements_no_filter_returns_all(view_browser_model) -> None:
    """F0: unfiltered list returns all six mock-aligned elements."""
    result = browse_service.list_elements(model_slug="yggdrasil", limit=50)
    names = {item["name"] for item in result.items}
    assert result.total == 6
    assert "Payment API" in names
    assert "Mobile App" in names


@pytest.mark.django_db
def test_list_elements_filter_package(view_browser_model) -> None:
    """F0: technology package filter excludes Context elements."""
    result = browse_service.list_elements(model_slug="yggdrasil", package="technology")
    names = {item["name"] for item in result.items}
    assert "Payment API" in names
    assert "Mobile App" not in names


@pytest.mark.django_db
def test_list_elements_filter_stereotype(view_browser_model) -> None:
    """F0: container stereotype filter returns only containers."""
    result = browse_service.list_elements(model_slug="yggdrasil", stereotype="container")
    names = {item["name"] for item in result.items}
    assert names == {"Payment API", "Notification Service"}


@pytest.mark.django_db
def test_subgraph_includes_edges_among_nodes(view_browser_model) -> None:
    """F0: subgraph JSON includes nodes and edges for filtered set."""
    payload = browse_service.subgraph_for_elements(
        model_slug="yggdrasil", package="technology", depth=2
    )
    assert len(payload["elements"]) >= 3
    assert len(payload["edges"]) >= 1


# -- W13: depth traversal BFS --


@pytest.mark.django_db
def test_resolve_root_element_ids_log_story_happy(view_browser_explorer_model, caplog) -> None:
    """Narrowing filters log why roots were chosen and which PKs matched."""
    ymodel = browse_service.resolve_model("yggdrasil")
    filters = browse_service.BrowseFilters(stereotype="component")
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.resolve_root_element_ids(ymodel, filters)
    assert_log_story(
        caplog,
        where="browse_service.resolve_root_element_ids",
        beats={
            "entry": ["model_slug=yggdrasil"],
            "branch": ["reason=narrowing_filters", "stereotype=component"],
            "processing": ["matched_pks=", "root_count="],
            "exit": ["root_count="],
        },
    )
    assert_log_story(
        caplog,
        where="browse_service._filtered_queryset",
        beats={"processing": ["stereotype=component", "model_slug=yggdrasil"]},
    )


@pytest.mark.django_db
def test_resolve_roots_from_stereotype_filter(view_browser_explorer_model) -> None:
    """W13: component filter roots exclude Redis."""
    ymodel = browse_service.resolve_model("yggdrasil")
    filters = browse_service.BrowseFilters(stereotype="component")
    root_ids = browse_service.resolve_root_element_ids(ymodel, filters)
    slugs = set(Element.objects.filter(pk__in=root_ids).values_list("slug", flat=True))
    assert {"auth", "munin", "graph"}.issubset(slugs)
    assert "redis" not in slugs


@pytest.mark.django_db
def test_resolve_roots_graph_sources_when_unfiltered(view_browser_model) -> None:
    """W13: unfiltered roots are graph sources, not all six payment elements."""
    ymodel = browse_service.resolve_model("yggdrasil")
    root_ids = browse_service.resolve_root_element_ids(ymodel, browse_service.BrowseFilters())
    assert len(root_ids) == 4
    slugs = set(Element.objects.filter(pk__in=root_ids).values_list("slug", flat=True))
    assert slugs == {
        "mobile-app",
        "notification-service",
        "order-domain",
        "fulfillment-worker",
    }


@pytest.mark.django_db
def test_bfs_depth_1_roots_only(view_browser_explorer_model) -> None:
    """W13: depth=1 component filter excludes Backend and Redis."""
    scoped = browse_service.subgraph_from_roots(
        model_slug="yggdrasil", stereotype="component", depth=1
    )
    slugs = {row["slug"] for row in scoped.node_summaries}
    assert "auth" in slugs
    assert "backend-web-celery" not in slugs
    assert "redis" not in slugs


@pytest.mark.django_db
def test_bfs_depth_2_one_hop(view_browser_explorer_model) -> None:
    """W13: depth=2 reaches llm/Backend but not Redis."""
    scoped = browse_service.subgraph_from_roots(
        model_slug="yggdrasil", stereotype="component", depth=2
    )
    slugs = {row["slug"] for row in scoped.node_summaries}
    assert "llm" in slugs or "backend-web-celery" in slugs
    assert "redis" not in slugs


@pytest.mark.django_db
def test_bfs_depth_3_two_hops(view_browser_explorer_model) -> None:
    """W13: depth=3 from component roots reaches Redis."""
    scoped = browse_service.subgraph_from_roots(
        model_slug="yggdrasil", stereotype="component", depth=3
    )
    slugs = {row["slug"] for row in scoped.node_summaries}
    assert "redis" in slugs


@pytest.mark.django_db
def test_bfs_cycle_visited_set(view_browser_user) -> None:
    """W13: cycle does not cause infinite BFS expansion."""
    from tests.fixtures.factories.model_factories import YggdrasilModelFactory

    from yggdrasil.changeset.models import ChangeSetItem
    from yggdrasil.graph.models import ensure_c4_metamodel
    from yggdrasil.mcp.server import set_current_user_id, set_token_scope
    from yggdrasil.mcp.tools.propose import propose_changeset

    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Cycle", slug="cycle", metamodel=mm)
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {"name": name, "stereotype_slug": "component", "package_slug": "application"},
            "confidence": 0.9,
        }
        for name in ("A", "B", "C")
    ]
    ops.extend(
        [
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": src,
                    "target_name": tgt,
                    "stereotype_slug": "depends_on",
                },
                "confidence": 0.9,
            }
            for src, tgt in [("A", "B"), ("B", "C"), ("C", "A")]
        ]
    )
    propose_changeset(model="cycle", operations=ops, run_id="run-cycle-fixture")
    from yggdrasil.graph.models import Element

    element_a = Element.objects.get(model=model, name="A")
    scoped = browse_service.bfs_from_element(element_a, direction="outgoing", depth=10)
    assert len(scoped.node_summaries) == 3


@pytest.mark.django_db
def test_subgraph_edges_both_endpoints_in_scope(view_browser_explorer_model) -> None:
    """W13: edges omitted when target is outside depth scope."""
    scoped = browse_service.subgraph_from_roots(
        model_slug="yggdrasil", stereotype="component", depth=1
    )
    id_set = {row["id"] for row in scoped.node_summaries}
    for edge in scoped.cytoscape_edges:
        assert int(edge["data"]["source"]) in id_set
        assert int(edge["data"]["target"]) in id_set


@pytest.mark.django_db
def test_compute_max_depth_capped_at_20(view_browser_user, monkeypatch, caplog) -> None:
    """W13: compute_max_depth respects MAX_DEPTH cap."""
    from tests.fixtures.factories.model_factories import YggdrasilModelFactory

    from yggdrasil.changeset.models import ChangeSetItem
    from yggdrasil.graph.models import Element, ensure_c4_metamodel
    from yggdrasil.mcp.server import set_current_user_id, set_token_scope
    from yggdrasil.mcp.tools.propose import propose_changeset

    monkeypatch.setattr(browse_service, "MAX_DEPTH", 3)
    set_current_user_id(view_browser_user.pk)
    set_token_scope("read-write")
    mm = ensure_c4_metamodel()
    model = YggdrasilModelFactory(name="Chain", slug="chain", metamodel=mm)
    ops = [
        {
            "op_type": ChangeSetItem.OP_ADD_ELEMENT,
            "detail": {
                "name": f"N{i}",
                "stereotype_slug": "component",
                "package_slug": "application",
            },
            "confidence": 0.9,
        }
        for i in range(5)
    ]
    ops.extend(
        [
            {
                "op_type": ChangeSetItem.OP_ADD_RELATIONSHIP,
                "detail": {
                    "source_name": f"N{i}",
                    "target_name": f"N{i + 1}",
                    "stereotype_slug": "depends_on",
                },
                "confidence": 0.9,
            }
            for i in range(4)
        ]
    )
    propose_changeset(model="chain", operations=ops, run_id="run-chain-fixture")
    root = Element.objects.get(model=model, name="N0")
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        result = browse_service.compute_max_depth(model, {root.pk})
    assert result == 3
    assert_log_story(
        caplog,
        where="browse_service.compute_max_depth",
        beats={
            "entry": ["root_count=", "cap="],
            "processing": ["visited_count=", "hops="],
            "exit": ["max_depth=", "capped="],
        },
    )


@pytest.mark.django_db
def test_bfs_subgraph_log_story_happy(view_browser_model, caplog) -> None:
    """W13: BFS subgraph emits entry, config, branch, processing, and exit beats."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.subgraph_from_roots(model_slug="yggdrasil", depth=1)
    assert_log_story(
        caplog,
        where="browse_service.subgraph_from_roots",
        beats={
            "entry": ["depth=", "direction=outgoing"],
            "config": ["stereotype=", "package=", "rel_stereotypes="],
            "branch": ["reason=all_induced_edges"],
            "processing": ["node_count=", "edge_count=", "root_pks=", "hops_requested="],
            "exit": ["max_depth="],
        },
    )
    assert_log_story(
        caplog,
        where="browse_service.resolve_root_element_ids",
        beats={
            "branch": ["reason=graph_sources", "root_pks=", "root_count="],
        },
    )
    assert_log_story(
        caplog,
        where="browse_service._bfs_expand",
        beats={"processing": ["start_count=", "hops_requested=", "visited="]},
    )


@pytest.mark.django_db
def test_format_node_label_log_story_happy(view_browser_explorer_model, caplog) -> None:
    """W15 log story: field_map label formatting logs element_id and path_count."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph"):
        browse_service.subgraph_from_roots(
            model_slug="yggdrasil",
            depth=2,
            stereotypes=("component",),
            field_map={"component": ["name", "owner"]},
        )
    assert_log_story(
        caplog,
        where="browse_service.format_node_label",
        beats={"processing": ["element_id=", "path_count="]},
    )


@pytest.mark.django_db
def test_bfs_subgraph_log_story_reject(view_browser_model, caplog) -> None:
    """W13: invalid depth logs error beat."""
    with (
        caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"),
        pytest.raises(ValueError, match="depth must be >= 1"),
    ):
        browse_service.subgraph_from_roots(model_slug="yggdrasil", depth=0)
    assert_log_story(
        caplog,
        where="browse_service.subgraph_from_roots",
        beats={"error": ["depth=0"]},
    )


@pytest.mark.django_db
def test_list_elements_log_story_happy(view_browser_model, caplog) -> None:
    """list_elements logs limit cap, filter branch, and returned counts."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.list_elements(model_slug="yggdrasil", package="technology", limit=50)
    assert_log_story(
        caplog,
        where="browse_service.list_elements",
        beats={
            "entry": ["model_slug=yggdrasil"],
            "validation": ["requested_limit=50", "capped="],
            "branch": ["reason=filtered", "package=technology"],
            "processing": ["total=", "returned="],
            "exit": ["returned_count="],
        },
    )


@pytest.mark.django_db
def test_list_elements_log_story_unfiltered(view_browser_model, caplog) -> None:
    """Unfiltered list_elements logs reason=unfiltered."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.list_elements(model_slug="yggdrasil", limit=500)
    assert_log_story(
        caplog,
        where="browse_service.list_elements",
        beats={
            "validation": ["requested_limit=500", "capped=True"],
            "branch": ["reason=unfiltered"],
        },
    )


@pytest.mark.django_db
def test_list_filter_options_log_story_happy(view_browser_model, caplog) -> None:
    """Filter dropdowns log package and stereotype counts."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.list_filter_options(model_slug="yggdrasil")
    assert_log_story(
        caplog,
        where="browse_service.list_filter_options",
        beats={
            "entry": ["model_slug=yggdrasil"],
            "exit": ["package_count=", "stereotype_count="],
        },
    )


@pytest.mark.django_db
def test_stereotype_field_catalog_log_story_happy(view_browser_model, caplog) -> None:
    """Catalog merge logs static-vs-base schema choice once."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.stereotype_field_catalog(model_slug="yggdrasil")
    assert_log_story(
        caplog,
        where="browse_service.stereotype_field_catalog",
        beats={
            "entry": ["model_slug=yggdrasil"],
            "processing": ["reason=", "static_count=", "base_count="],
            "exit": ["stereotype_count="],
        },
    )


@pytest.mark.django_db
def test_list_all_element_summaries_log_story_happy(view_browser_model, caplog) -> None:
    """Navigator summaries log entry and element_count."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.list_all_element_summaries(model_slug="yggdrasil")
    assert_log_story(
        caplog,
        where="browse_service.list_all_element_summaries",
        beats={
            "entry": ["model_slug=yggdrasil"],
            "exit": ["element_count="],
        },
    )


@pytest.mark.django_db
def test_build_package_scoped_filter_options_log_story_no_packages(
    view_browser_model, caplog
) -> None:
    """Empty package selection returns base options with reason=no_packages."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.build_package_scoped_filter_options(model_slug="yggdrasil", packages=())
    assert_log_story(
        caplog,
        where="browse_service.build_package_scoped_filter_options",
        beats={
            "entry": ["package_count=0"],
            "branch": ["reason=no_packages"],
        },
    )


@pytest.mark.django_db
def test_build_package_scoped_filter_options_log_story_scoped(view_browser_model, caplog) -> None:
    """Package-scoped options log reason=scoped."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.build_package_scoped_filter_options(
            model_slug="yggdrasil", packages=("technology",)
        )
    assert_log_story(
        caplog,
        where="browse_service.build_package_scoped_filter_options",
        beats={
            "entry": ["package_count=1"],
            "branch": ["reason=scoped"],
        },
    )


@pytest.mark.django_db
def test_resolve_model_log_story_happy(view_browser_model, caplog) -> None:
    """Successful model resolve logs model_id and slug."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.resolve_model("yggdrasil")
    assert_log_story(
        caplog,
        where="browse_service.resolve_model",
        beats={"exit": ["model_id=", "slug=yggdrasil"]},
    )


@pytest.mark.django_db
def test_resolve_model_log_story_reject(caplog) -> None:
    """Missing model logs reason=not_found."""
    with (
        caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"),
        pytest.raises(ValueError, match="not found"),
    ):
        browse_service.resolve_model("missing-model")
    assert_log_story(
        caplog,
        where="browse_service.resolve_model",
        beats={"error": ["reason=not_found", "model_slug=missing-model"]},
    )


@pytest.mark.django_db
def test_bfs_from_element_log_story_happy(view_browser_model, caplog) -> None:
    """Single-element BFS logs adjacency choice and visited count."""
    element = Element.objects.filter(model__slug="yggdrasil").order_by("name").first()
    assert element is not None
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.bfs_from_element(element, direction="outgoing", depth=2)
    assert_log_story(
        caplog,
        where="browse_service.bfs_from_element",
        beats={
            "entry": ["element_id=", "direction=outgoing", "depth=2"],
            "branch": ["reason=outgoing_adjacency"],
            "processing": ["visited="],
            "exit": ["node_count="],
        },
    )


@pytest.mark.django_db
def test_bfs_from_element_log_story_reject(view_browser_model, caplog) -> None:
    """Invalid BFS depth logs reason=invalid_depth."""
    element = Element.objects.filter(model__slug="yggdrasil").first()
    assert element is not None
    with (
        caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"),
        pytest.raises(ValueError, match="depth must be >= 1"),
    ):
        browse_service.bfs_from_element(element, direction="outgoing", depth=0)
    assert_log_story(
        caplog,
        where="browse_service.bfs_from_element",
        beats={
            "entry": ["element_id=", "depth=0"],
            "validation": ["reason=invalid_depth"],
        },
    )


@pytest.mark.django_db
def test_subgraph_for_elements_log_story_legacy(view_browser_model, caplog) -> None:
    """Legacy PK list uses reason=legacy_element_ids."""
    ids = list(Element.objects.filter(model__slug="yggdrasil").values_list("pk", flat=True)[:2])
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.subgraph_for_elements(model_slug="yggdrasil", element_ids=ids)
    assert_log_story(
        caplog,
        where="browse_service.subgraph_for_elements",
        beats={
            "branch": ["reason=legacy_element_ids"],
            "exit": ["node_count=", "edge_count="],
        },
    )


@pytest.mark.django_db
def test_subgraph_for_elements_log_story_depth_bfs(view_browser_model, caplog) -> None:
    """Default subgraph path uses reason=depth_bfs."""
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph.browse"):
        browse_service.subgraph_for_elements(model_slug="yggdrasil", depth=1)
    assert_log_story(
        caplog,
        where="browse_service.subgraph_for_elements",
        beats={
            "branch": ["reason=depth_bfs"],
            "exit": ["node_count="],
        },
    )


@pytest.mark.django_db
def test_list_elements_mcp_delegates_to_service(view_browser_model, view_browser_user) -> None:
    """F0: MCP list_elements returns same count via shared service."""
    from yggdrasil.mcp.server import set_current_user_id

    set_current_user_id(view_browser_user.pk)
    mcp_result = mcp_list_elements(model="yggdrasil", limit=50)
    assert mcp_result["total"] == 6
    assert any(item["name"] == "Payment API" for item in mcp_result["items"])
