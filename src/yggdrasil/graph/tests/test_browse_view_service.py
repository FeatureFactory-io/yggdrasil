"""Tests for graph browse_view_service (W14 Named Views persistence)."""

from __future__ import annotations

import logging

import pytest
from django.core.exceptions import ValidationError
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_view_service
from yggdrasil.graph.models import BrowseView, ensure_c4_metamodel


def _sample_payload_v1(*, package: str = "technology", depth: int = 2) -> dict:
    """Minimal v1 BrowseView payload for tests."""
    return {
        "filters": {
            "packages": [package],
            "element_stereotypes": [],
            "relationship_stereotypes": [],
        },
        "levels": {"depth": depth},
        "presentation": "graph",
    }


@pytest.fixture
def browse_view_model(db):
    """Readable Yggdrasil model for BrowseView tests."""
    ensure_c4_metamodel()
    return YggdrasilModelFactory(name="Yggdrasil", slug="yggdrasil")


@pytest.fixture
def other_model(db):
    """Second model for catalog scoping tests."""
    ensure_c4_metamodel()
    return YggdrasilModelFactory(name="Payments", slug="payments")


@pytest.mark.django_db
def test_save_browse_view_creates_record(browse_view_model) -> None:
    """W14-1: save_view persists ORM row with slug unique per model+owner."""
    owner = UserFactory(is_architect=True)
    saved = browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Tech only",
        payload=_sample_payload_v1(),
    )
    assert saved.pk is not None
    assert saved.slug == "tech-only"
    assert saved.name == "Tech only"
    assert BrowseView.objects.filter(model=browse_view_model, owner=owner).count() == 1


@pytest.mark.django_db
def test_save_browse_view_rejects_duplicate_slug(browse_view_model) -> None:
    """W14-1: duplicate slug for same model+owner raises ValidationError."""
    owner = UserFactory(is_architect=True)
    browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Tech only",
        payload=_sample_payload_v1(),
    )
    with pytest.raises(ValidationError):
        browse_view_service.save_view(
            owner,
            browse_view_model,
            name="Tech only",
            payload=_sample_payload_v1(package="application"),
        )


@pytest.mark.django_db
def test_list_browse_views_scoped_to_model_and_owner(browse_view_model, other_model) -> None:
    """W14-1: catalog lists only current user's views on the active model."""
    owner = UserFactory(is_architect=True)
    other_user = UserFactory(is_architect=True)
    browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Ygg view",
        payload=_sample_payload_v1(),
    )
    browse_view_service.save_view(
        owner,
        other_model,
        name="Payments view",
        payload=_sample_payload_v1(package="application"),
    )
    browse_view_service.save_view(
        other_user,
        browse_view_model,
        name="Other architect view",
        payload=_sample_payload_v1(package="context"),
    )
    slugs = {view.slug for view in browse_view_service.list_views(owner, browse_view_model)}
    assert slugs == {"ygg-view"}


@pytest.mark.django_db
def test_expand_browse_view_to_query_string(browse_view_model) -> None:
    """W14-1: expand_to_query_params maps payload v1 to URL query lists."""
    owner = UserFactory(is_architect=True)
    saved = browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Payment review",
        payload={
            "filters": {
                "packages": ["technology"],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": ["depends_on"],
            },
            "levels": {"depth": 2},
            "presentation": "graph",
        },
    )
    params = browse_view_service.expand_to_query_params(saved)
    assert params["package"] == ["technology"]
    assert params["stereotype"] == ["component"]
    assert params["edge_stereotype"] == ["depends_on"]
    assert params["depth"] == ["2"]
    assert params["mode"] == ["graph"]


@pytest.mark.django_db
def test_expand_payload_includes_field_map(browse_view_model) -> None:
    """W15: expand_to_query_params emits field_{stereotype} lists."""
    owner = UserFactory(is_architect=True)
    saved = browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Fields",
        payload={
            "filters": {
                "packages": [],
                "element_stereotypes": ["component"],
                "relationship_stereotypes": [],
            },
            "levels": {"depth": 1},
            "presentation": "graph",
            "content": {"field_map": {"component": ["name", "owner"]}},
        },
    )
    params = browse_view_service.expand_to_query_params(saved)
    assert params["field_component"] == ["name", "owner"]


@pytest.mark.django_db
def test_delete_browse_view_owner_only(browse_view_model) -> None:
    """W14-1: only the owner may delete their saved View."""
    owner = UserFactory(is_architect=True)
    viewer = UserFactory(is_viewer=True)
    saved = browse_view_service.save_view(
        owner,
        browse_view_model,
        name="Temporary",
        payload=_sample_payload_v1(),
    )
    with pytest.raises(PermissionError):
        browse_view_service.delete_view(viewer, browse_view_model, saved.slug)
    browse_view_service.delete_view(owner, browse_view_model, saved.slug)
    assert not BrowseView.objects.filter(pk=saved.pk).exists()


@pytest.mark.django_db
def test_payload_v1_roundtrip(browse_view_model) -> None:
    """W14-1: validated payload round-trips through save and reload."""
    owner = UserFactory(is_architect=True)
    payload = _sample_payload_v1(package="application", depth=3)
    payload["presentation"] = "table"
    saved = browse_view_service.save_view(
        owner,
        browse_view_model,
        name="App table",
        payload=payload,
    )
    loaded = browse_view_service.get_view(owner, browse_view_model, saved.slug)
    assert loaded.payload == payload


@pytest.mark.django_db
def test_save_browse_view_log_story_happy(browse_view_model, caplog) -> None:
    """W14-1 log story: save_view entry → processing → exit with slug=."""
    owner = UserFactory(is_architect=True)
    with caplog.at_level(logging.INFO, logger="yggdrasil.graph"):
        browse_view_service.save_view(
            owner,
            browse_view_model,
            name="Tech stack",
            payload=_sample_payload_v1(),
        )
    assert_log_story(
        caplog,
        where="BrowseViewService.save_view",
        beats={
            "entry": ["user_pk=", "model_slug=", "name="],
            "exit": ["slug=", "browse_view_id="],
        },
    )


@pytest.mark.django_db
def test_save_browse_view_log_story_reject(browse_view_model, caplog) -> None:
    """W14-1 log story: validation reject on empty name."""
    owner = UserFactory(is_architect=True)
    with (
        caplog.at_level(logging.INFO, logger="yggdrasil.graph"),
        pytest.raises(ValidationError),
    ):
        browse_view_service.save_view(
            owner,
            browse_view_model,
            name="   ",
            payload=_sample_payload_v1(),
        )
    assert_log_story(
        caplog,
        where="BrowseViewService.save_view",
        beats={
            "validation": ["reason="],
        },
    )
