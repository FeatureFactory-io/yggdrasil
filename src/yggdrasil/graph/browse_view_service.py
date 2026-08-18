"""
BrowseView persistence for named View Browser snapshots (W14).

ORM writes only — not ChangeSet-governed (Views v1 Q2).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.utils.text import slugify

from yggdrasil.graph.models import BrowseView, YggdrasilModel

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser
    from django.db.models import QuerySet

logger = logging.getLogger("yggdrasil.graph")

VALID_PRESENTATIONS = frozenset({"graph", "table"})


def validate_payload_v1(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize a BrowseView payload v1.

    :param payload: Raw JSON payload from save or load.
    :return: Normalized payload with ``filters``, ``levels``, ``presentation``.
    :raises ValidationError: When required keys or types are invalid.
    """
    if not isinstance(payload, dict):
        raise ValidationError({"payload": "Payload must be a JSON object."})

    filters = payload.get("filters")
    if not isinstance(filters, dict):
        raise ValidationError({"filters": "filters must be an object."})

    normalized_filters = {
        "packages": _coerce_str_list(filters.get("packages")),
        "element_stereotypes": _coerce_str_list(filters.get("element_stereotypes")),
        "relationship_stereotypes": _coerce_str_list(filters.get("relationship_stereotypes")),
    }

    levels = payload.get("levels")
    if not isinstance(levels, dict):
        raise ValidationError({"levels": "levels must be an object."})
    try:
        depth = int(levels.get("depth", 1))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"levels.depth": "depth must be an integer."}) from exc
    if depth < 1:
        raise ValidationError({"levels.depth": "depth must be >= 1."})

    presentation = payload.get("presentation", "graph")
    if presentation not in VALID_PRESENTATIONS:
        raise ValidationError({"presentation": f"Must be one of {sorted(VALID_PRESENTATIONS)}."})

    normalized: dict[str, Any] = {
        "filters": normalized_filters,
        "levels": {"depth": depth},
        "presentation": presentation,
    }
    if "content" in payload and isinstance(payload["content"], dict):
        normalized["content"] = payload["content"]
    if "viewport" in payload and payload["viewport"] is not None:
        normalized["viewport"] = payload["viewport"]
    return normalized


def save_view(
    user: AbstractBaseUser,
    model: YggdrasilModel,
    name: str,
    payload: dict[str, Any],
) -> BrowseView:
    """
    Create or update a named BrowseView for the given user and Model.

    :param user: Owning user (architect).
    :param model: Target YggdrasilModel.
    :param name: Human-readable View name. Example: ``"Tech only"``.
    :param payload: v1 payload (``filters``, ``levels``, ``presentation``).
    :return: Persisted BrowseView instance.
    :raises ValidationError: Empty name, invalid payload, or duplicate slug.
    """
    logger.info(
        "BrowseViewService.save_view | entry | user_pk=%s model_slug=%s name=%s",
        user.pk,
        model.slug,
        name,
    )
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        logger.info(
            "BrowseViewService.save_view | validation | user_pk=%s model_slug=%s reason=empty_name",
            user.pk,
            model.slug,
        )
        raise ValidationError({"name": "View name is required."})

    normalized_payload = validate_payload_v1(payload)
    slug = slugify(cleaned_name)
    if BrowseView.objects.filter(model=model, owner=user, slug=slug).exists():
        logger.info(
            "BrowseViewService.save_view | validation | user_pk=%s model_slug=%s reason=duplicate_slug slug=%s",
            user.pk,
            model.slug,
            slug,
        )
        raise ValidationError({"slug": f"A View named '{cleaned_name}' already exists."})

    view = BrowseView.objects.create(
        model=model,
        owner=user,
        name=cleaned_name,
        slug=slug,
        payload=normalized_payload,
    )
    logger.info(
        "BrowseViewService.save_view | exit | user_pk=%s model_slug=%s slug=%s browse_view_id=%s",
        user.pk,
        model.slug,
        view.slug,
        view.pk,
    )
    return view


def list_views(user: AbstractBaseUser, model: YggdrasilModel) -> QuerySet[BrowseView]:
    """
    List saved Views owned by ``user`` on ``model``.

    :param user: Catalog owner.
    :param model: Active YggdrasilModel.
    :return: QuerySet ordered by name.
    """
    return BrowseView.objects.filter(model=model, owner=user).order_by("name")


def resolve_view_for_load(
    user: AbstractBaseUser,
    model: YggdrasilModel,
    slug: str,
) -> BrowseView | None:
    """
    Resolve a named View for load — prefer the current user's row, else any on the Model.

    :param user: Authenticated reader.
    :param model: Active YggdrasilModel.
    :param slug: View slug from ``?browse_view=``.
    :return: Matching BrowseView or None when not found.
    """
    owned = BrowseView.objects.filter(model=model, owner=user, slug=slug).first()
    if owned is not None:
        return owned
    shared = BrowseView.objects.filter(model=model, slug=slug).order_by("name").first()
    if shared is None:
        logger.info(
            "BrowseViewService.resolve_view_for_load | branch | user_pk=%s model_slug=%s slug=%s reason=not_found",
            user.pk,
            model.slug,
            slug,
        )
    return shared


def get_view(user: AbstractBaseUser, model: YggdrasilModel, slug: str) -> BrowseView:
    """
    Load a saved View by slug for the given owner and Model.

    :param user: View owner.
    :param model: Active YggdrasilModel.
    :param slug: URL-safe View slug. Example: ``"tech-only"``.
    :return: Matching BrowseView.
    :raises BrowseView.DoesNotExist: When no row matches.
    """
    return BrowseView.objects.get(model=model, owner=user, slug=slug)


def delete_view(user: AbstractBaseUser, model: YggdrasilModel, slug: str) -> None:
    """
    Delete a saved View; owner-only (Views v1 Q3).

    :param user: Acting user (must be owner).
    :param model: Active YggdrasilModel.
    :param slug: View slug to delete.
    :raises PermissionError: When ``user`` is not the View owner.
    :raises BrowseView.DoesNotExist: When no row matches.
    """
    view = BrowseView.objects.get(model=model, slug=slug)
    if view.owner_id != user.pk:
        logger.info(
            "BrowseViewService.delete_view | validation | user_pk=%s model_slug=%s slug=%s reason=not_owner",
            user.pk,
            model.slug,
            slug,
        )
        raise PermissionError("Only the View owner may delete this View.")
    view.delete()
    logger.info(
        "BrowseViewService.delete_view | exit | user_pk=%s model_slug=%s slug=%s deleted=true",
        user.pk,
        model.slug,
        slug,
    )


def expand_to_query_params(view: BrowseView) -> dict[str, list[str]]:
    """
    Expand a saved View payload v1 into multi-value query param lists.

    :param view: Persisted BrowseView row.
    :return: Query param dict (``package``, ``stereotype``, ``depth``, ``mode``, …).
    """
    logger.info(
        "BrowseViewService.expand_to_query_params | entry | slug=%s model_slug=%s user_pk=%s",
        view.slug,
        view.model.slug,
        view.owner_id,
    )
    payload = validate_payload_v1(view.payload)
    filters = payload["filters"]
    params: dict[str, list[str]] = {}
    if filters["packages"]:
        params["package"] = list(filters["packages"])
    if filters["element_stereotypes"]:
        params["stereotype"] = list(filters["element_stereotypes"])
    if filters["relationship_stereotypes"]:
        params["edge_stereotype"] = list(filters["relationship_stereotypes"])
    params["depth"] = [str(payload["levels"]["depth"])]
    params["mode"] = [payload["presentation"]]
    logger.info(
        "BrowseViewService.expand_to_query_params | exit | slug=%s depth=%s mode=%s",
        view.slug,
        params["depth"][0],
        params["mode"][0],
    )
    return params


def _coerce_str_list(raw: Any) -> list[str]:
    """Normalize filter list values to non-empty strings."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValidationError({"filters": "Filter lists must be arrays."})
    return [str(item).strip() for item in raw if str(item).strip()]
