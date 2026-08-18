"""Web tests for VIEW-BROWSE-1 Named Views (W14)."""

from __future__ import annotations

import logging

import pytest
from django.urls import reverse
from tests.fixtures.factories import UserFactory
from tests.fixtures.factories.model_factories import YggdrasilModelFactory
from tests.support.log_story import assert_log_story

from yggdrasil.graph import browse_view_service
from yggdrasil.graph.models import BrowseView


def _browse_url(model_slug: str = "yggdrasil") -> str:
    return reverse("web:view_browse_model", kwargs={"model_slug": model_slug})


def _save_url(model_slug: str = "yggdrasil") -> str:
    return reverse("web:view_browse_save", kwargs={"model_slug": model_slug})


def _delete_url(model_slug: str, view_slug: str) -> str:
    return reverse(
        "web:view_browse_delete",
        kwargs={"model_slug": model_slug, "view_slug": view_slug},
    )


def _payload_v1(*, package: str = "", stereotype: str = "", depth: int = 1, mode: str = "graph"):
    return {
        "filters": {
            "packages": [package] if package else [],
            "element_stereotypes": [stereotype] if stereotype else [],
            "relationship_stereotypes": [],
        },
        "levels": {"depth": depth},
        "presentation": mode,
    }


@pytest.mark.django_db
def test_save_view_post_creates_browse_view(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-62: POST save creates BrowseView and redirects to browse_view=."""
    client.force_login(view_browser_user)
    response = client.post(
        _save_url(),
        {
            "name": "Tech only",
            "package": "technology",
            "depth": "2",
            "mode": "graph",
        },
    )
    assert response.status_code == 302
    assert "browse_view=tech-only" in response["Location"]
    view = BrowseView.objects.get(model=view_browser_model, owner=view_browser_user)
    assert view.slug == "tech-only"
    assert view.payload["filters"]["packages"] == ["technology"]
    assert view.payload["levels"]["depth"] == 2


@pytest.mark.django_db
def test_browse_view_slug_loads_equivalent_filters(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-64: GET ?browse_view= expands saved filters."""
    browse_view_service.save_view(
        view_browser_user,
        view_browser_model,
        name="Payment review",
        payload=_payload_v1(package="technology", depth=2),
    )
    client.force_login(view_browser_user)
    response = client.get(_browse_url(), {"browse_view": "payment-review"})
    assert response.status_code == 200
    body = response.content.decode()
    assert "Payment API" in body
    assert "Notification Service" in body
    assert "Order Domain" not in body


@pytest.mark.django_db
def test_viewer_cannot_save_view(client, view_browser_model):
    """VIEW-BROWSE-1-68: viewer role does not see save affordances."""
    viewer = UserFactory(is_viewer=True)
    client.force_login(viewer)
    response = client.get(_browse_url())
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="save-view-btn"' not in body
    assert 'data-testid="save-view-confirm-btn"' not in body


@pytest.mark.django_db
def test_view_browse_save_log_story_happy(client, view_browser_user, view_browser_model, caplog):
    """W14 log story: ViewBrowseSaveView.post exit with slug=."""
    client.force_login(view_browser_user)
    with caplog.at_level(logging.INFO, logger="yggdrasil.web"):
        client.post(
            _save_url(),
            {"name": "Stack", "package": "technology", "depth": "2", "mode": "graph"},
        )
    assert_log_story(
        caplog,
        where="ViewBrowseSaveView.post",
        beats={
            "entry": ["user_pk=", "model_slug="],
            "exit": ["slug=", "model_slug="],
        },
    )


@pytest.mark.django_db
def test_delete_view_post_removes_browse_view(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-66: owner POST delete removes View from catalog."""
    saved = browse_view_service.save_view(
        view_browser_user,
        view_browser_model,
        name="Temporary",
        payload=_payload_v1(),
    )
    client.force_login(view_browser_user)
    response = client.post(_delete_url("yggdrasil", saved.slug))
    assert response.status_code == 302
    assert not BrowseView.objects.filter(pk=saved.pk).exists()


@pytest.mark.django_db
def test_browse_views_scoped_to_model_in_context(client, view_browser_user, view_browser_model):
    """VIEW-BROWSE-1-65: dropdown lists only views on current model."""
    other_model = YggdrasilModelFactory(
        name="Payments",
        slug="payments",
        metamodel=view_browser_model.metamodel,
    )
    browse_view_service.save_view(
        view_browser_user,
        view_browser_model,
        name="Ygg view",
        payload=_payload_v1(),
    )
    browse_view_service.save_view(
        view_browser_user,
        other_model,
        name="Payments view",
        payload=_payload_v1(package="technology"),
    )
    client.force_login(view_browser_user)
    response = client.get(_browse_url("yggdrasil"))
    body = response.content.decode()
    assert 'data-testid="view-option-ygg-view"' in body
    assert 'data-testid="view-option-payments-view"' not in body
