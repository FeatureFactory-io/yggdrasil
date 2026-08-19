"""Unit tests for browse_helpers (W7 + W13)."""

from __future__ import annotations

import logging

import pytest
from django.test import RequestFactory
from tests.fixtures.factories import UserFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_view_service
from yggdrasil.web.browse_helpers import (
    DEFAULT_VIEW_MODE,
    apply_browse_view_expansion,
    build_package_tree,
    build_traversal_tree,
    build_view_browse_context,
    parse_browse_params_from_post,
    parse_view_browse_params,
    user_can_save_views,
)


def test_build_package_tree_groups_and_orders_packages() -> None:
    """Package tree orders Context → Application → Technology."""
    elements = [
        {"name": "Redis", "package": "Technology", "package_slug": "technology", "slug": "redis"},
        {"name": "auth", "package": "Application", "package_slug": "application", "slug": "auth"},
        {"name": "Yggdrasil", "package": "Context", "package_slug": "context", "slug": "yggdrasil"},
    ]
    tree = build_package_tree(elements)
    assert [node["slug"] for node in tree] == ["context", "application", "technology"]
    assert tree[1]["elements"][0]["name"] == "auth"


def test_parse_depth_defaults_to_1() -> None:
    """W13: omitted depth query param defaults to 1."""
    request = RequestFactory().get("/models/yggdrasil/views/")
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.depth == 1


def test_parse_view_defaults_to_graph() -> None:
    """Omitted mode/view query param defaults to graph presentation."""
    request = RequestFactory().get("/models/yggdrasil/views/")
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == DEFAULT_VIEW_MODE
    assert params.view_mode == "graph"


def test_parse_mode_query_param_table() -> None:
    """W14-0: ``?mode=table`` selects table presentation."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"mode": "table"})
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_parse_mode_prefers_mode_over_legacy_view() -> None:
    """W14-0: ``?mode=`` wins when both ``mode`` and legacy ``view`` are present."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        {"mode": "table", "view": "graph"},
    )
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_parse_legacy_view_query_param_fallback() -> None:
    """W14-0: legacy ``?view=`` still works as alias for ``?mode=``."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"view": "table"})
    params = parse_view_browse_params(request, "yggdrasil")
    assert params.view_mode == "table"


def test_parse_view_browse_params_log_story_happy(caplog) -> None:
    """W15 log story: parse_view_browse_params logs field_map counts."""
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        [("field_component", "name"), ("field_component", "owner")],
    )
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        parse_view_browse_params(request, "yggdrasil")
    assert_log_story(
        caplog,
        where="browse_helpers.parse_view_browse_params",
        beats={
            "entry": ["model_slug="],
            "config": ["packages=", "stereotypes=", "depth=", "mode="],
            "processing": ["field_stereotypes=", "field_path_count="],
        },
    )


@pytest.mark.django_db
def test_apply_browse_view_expansion_log_story_happy(view_browser_model, caplog) -> None:
    """W14/W15 log story: browse_view expansion resolves field_map from payload."""
    owner = UserFactory(is_architect=True)
    browse_view_service.save_view(
        owner,
        view_browser_model,
        name="Field map view",
        payload={
            "filters": {
                "packages": [],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 2},
            "presentation": "graph",
            "content": {"field_map": {"component": ["name", "owner"]}},
        },
    )
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        {"browse_view": "field-map-view"},
    )
    request.user = owner
    params = parse_view_browse_params(request, "yggdrasil")
    with caplog.at_level(logging.INFO):
        merged = apply_browse_view_expansion(request, owner, view_browser_model, params)
    assert merged.loaded_view_name == "Field map view"
    assert_log_story(
        caplog,
        where="browse_helpers.apply_browse_view_expansion",
        beats={
            "entry": ["browse_view=", "model_slug=", "user_pk="],
            "expanded": ["reason=expanded"],
            "exit": ["expanded=true", "depth="],
        },
    )
    assert_log_story(
        caplog,
        where="browse_content.resolve_field_map",
        beats={"processing": ["source=payload", "field_stereotypes=", "field_path_count="]},
    )


def test_build_traversal_tree_nests_children() -> None:
    """W13: parent/child nesting from BFS parent map."""
    rows = [
        {"id": 1, "name": "munin", "slug": "munin", "stereotype": "Component", "health": "green"},
        {"id": 2, "name": "llm", "slug": "llm", "stereotype": "Component", "health": "green"},
    ]
    parent_map = {1: None, 2: 1}
    tree = build_traversal_tree(rows, parent_map, frozenset({1}))
    assert len(tree) == 1
    assert tree[0]["slug"] == "munin"
    assert tree[0]["children"][0]["slug"] == "llm"


def test_build_traversal_tree_log_story_happy(caplog) -> None:
    """W13: traversal tree build logs tree_root_count."""
    rows = [
        {"id": 1, "name": "auth", "slug": "auth", "stereotype": "Component", "health": "green"},
    ]
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        build_traversal_tree(rows, {1: None}, frozenset({1}))
    assert_log_story(
        caplog,
        where="build_traversal_tree",
        beats={
            "exit": ["tree_root_count=", "element_count="],
        },
    )


@pytest.mark.django_db
def test_build_view_browse_context_includes_slugs_and_traversal(view_browser_model) -> None:
    """build_view_browse_context rows include slug fields and traversal tree."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/", {"depth": "3"})
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    context = build_view_browse_context(request, params)
    assert context["element_count"] == 6
    assert context["traversal_roots"]
    assert context["current_depth"] == 3
    assert context["model_name"] == "Yggdrasil"
    row = context["elements"][0]
    for key in ("slug", "stereotype_slug", "package_slug"):
        assert row.get(key)


@pytest.mark.django_db
def test_build_view_browse_context_returns_traversal_fields(view_browser_model) -> None:
    """Context includes traversal_roots and model_name from resolve_model."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/")
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    context = build_view_browse_context(request, params)
    assert context["traversal_roots"]
    assert context["model_name"] == "Yggdrasil"
    assert context["element_count"] == 4


def test_parse_depth_log_story_default(caplog) -> None:
    """Omitted depth logs reason=default."""
    request = RequestFactory().get("/models/yggdrasil/views/")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        parse_view_browse_params(request, "yggdrasil")
    assert_log_story(
        caplog,
        where="browse_helpers._parse_depth",
        beats={"default": ["reason=default"]},
    )


def test_parse_depth_log_story_invalid(caplog) -> None:
    """Non-integer depth logs reason=invalid."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"depth": "abc"})
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        params = parse_view_browse_params(request, "yggdrasil")
    assert params.depth == 1
    assert_log_story(
        caplog,
        where="browse_helpers._parse_depth",
        beats={"invalid": ["reason=invalid"]},
    )


def test_parse_depth_log_story_parsed(caplog) -> None:
    """Numeric depth logs reason=parsed."""
    request = RequestFactory().get("/models/yggdrasil/views/", {"depth": "3"})
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        params = parse_view_browse_params(request, "yggdrasil")
    assert params.depth == 3
    assert_log_story(
        caplog,
        where="browse_helpers._parse_depth",
        beats={"parsed": ["reason=parsed", "depth=3"]},
    )


@pytest.mark.django_db
def test_apply_browse_view_expansion_log_story_not_found(view_browser_model, caplog) -> None:
    """Missing saved View logs reason=not_found (was silent)."""
    owner = UserFactory(is_architect=True)
    request = RequestFactory().get(
        "/models/yggdrasil/views/",
        {"browse_view": "does-not-exist"},
    )
    request.user = owner
    params = parse_view_browse_params(request, "yggdrasil")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        merged = apply_browse_view_expansion(request, owner, view_browser_model, params)
    assert merged.browse_view is None
    assert_log_story(
        caplog,
        where="browse_helpers.apply_browse_view_expansion",
        beats={"not_found": ["reason=not_found", "browse_view=does-not-exist"]},
    )


@pytest.mark.django_db
def test_apply_browse_view_expansion_log_story_no_browse_view(view_browser_model, caplog) -> None:
    """No browse_view query param logs reason=no_browse_view."""
    owner = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/")
    request.user = owner
    params = parse_view_browse_params(request, "yggdrasil")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        apply_browse_view_expansion(request, owner, view_browser_model, params)
    assert_log_story(
        caplog,
        where="browse_helpers.apply_browse_view_expansion",
        beats={"none": ["reason=no_browse_view"]},
    )


def test_parse_viewport_invalid_json_log_story(caplog) -> None:
    """Invalid viewport JSON logs reason=invalid_json."""
    request = RequestFactory().post(
        "/models/yggdrasil/views/save/",
        {"viewport": "{not-json"},
    )
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        params = parse_browse_params_from_post(request, "yggdrasil")
    assert params.viewport is None
    assert_log_story(
        caplog,
        where="browse_helpers._parse_viewport_from_post",
        beats={"invalid": ["reason=invalid_json"]},
    )


@pytest.mark.django_db
def test_user_can_save_views_log_story_denied(caplog) -> None:
    """Viewer is denied with reason=denied."""
    viewer = UserFactory(is_viewer=True)
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        assert user_can_save_views(viewer) is False
    assert_log_story(
        caplog,
        where="browse_helpers.user_can_save_views",
        beats={"denied": ["reason=denied"]},
    )


@pytest.mark.django_db
def test_user_can_save_views_log_story_architect(caplog) -> None:
    """Architect is allowed with reason=architect."""
    from django.contrib.auth.models import Group

    architect = UserFactory()
    group, _ = Group.objects.get_or_create(name="architect")
    architect.groups.add(group)
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        assert user_can_save_views(architect) is True
    assert_log_story(
        caplog,
        where="browse_helpers.user_can_save_views",
        beats={"architect": ["reason=architect"]},
    )


@pytest.mark.django_db
def test_user_can_save_views_log_story_superuser(caplog) -> None:
    """Superuser is allowed with reason=superuser."""
    admin = UserFactory(is_admin=True)
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        assert user_can_save_views(admin) is True
    assert_log_story(
        caplog,
        where="browse_helpers.user_can_save_views",
        beats={"superuser": ["reason=superuser"]},
    )


@pytest.mark.django_db
def test_load_browse_subgraph_log_story_navigator(view_browser_model, caplog) -> None:
    """Default scope uses package navigator."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/")
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        build_view_browse_context(request, params)
    assert_log_story(
        caplog,
        where="browse_helpers._load_browse_subgraph",
        beats={"navigator": ["reason=package_navigator"]},
    )


@pytest.mark.django_db
def test_load_browse_subgraph_log_story_traversal(view_browser_model, caplog) -> None:
    """Filtered/depth scope uses traversal tree."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/yggdrasil/views/", {"depth": "3"})
    request.user = user
    params = parse_view_browse_params(request, "yggdrasil")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        build_view_browse_context(request, params)
    assert_log_story(
        caplog,
        where="browse_helpers._load_browse_subgraph",
        beats={"tree": ["reason=traversal_tree"]},
    )


@pytest.mark.django_db
def test_load_browse_subgraph_log_story_model_not_found(caplog) -> None:
    """Unknown model slug logs reason=model_not_found."""
    user = UserFactory(is_architect=True)
    request = RequestFactory().get("/models/missing/views/")
    request.user = user
    params = parse_view_browse_params(request, "missing-model")
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        context = build_view_browse_context(request, params)
    assert context["element_count"] == 0
    assert_log_story(
        caplog,
        where="browse_helpers._load_browse_subgraph",
        beats={"missing": ["reason=model_not_found"]},
    )
