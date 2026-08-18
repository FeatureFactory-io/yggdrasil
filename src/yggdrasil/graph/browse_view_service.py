"""
BrowseView persistence for named View Browser snapshots (W14).

ORM writes only — not ChangeSet-governed (Views v1 Q2).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from django.core.exceptions import ValidationError
from django.utils.text import slugify

from yggdrasil.graph.models import BrowseView, YggdrasilModel

if TYPE_CHECKING:
    from django.contrib.auth.models import User
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

    normalized: dict[str, Any] = {
        "filters": _normalize_filters(payload.get("filters")),
        "levels": _normalize_levels(payload.get("levels")),
        "presentation": _normalize_presentation(payload.get("presentation", "graph")),
    }
    _attach_optional_payload_sections(payload, normalized)
    return normalized


def save_view(
    user: User,
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
    cleaned_name = _validated_view_name(user, model, name)
    normalized_payload = validate_payload_v1(payload)
    slug = slugify(cleaned_name)
    _reject_duplicate_slug(user, model, slug, cleaned_name)
    return _create_browse_view(user, model, cleaned_name, slug, normalized_payload)


def _create_browse_view(
    user: User,
    model: YggdrasilModel,
    cleaned_name: str,
    slug: str,
    normalized_payload: dict[str, Any],
) -> BrowseView:
    """Persist a new BrowseView row and log exit beat."""
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


def list_views(user: User, model: YggdrasilModel) -> QuerySet[BrowseView]:
    """
    List saved Views owned by ``user`` on ``model``.

    :param user: Catalog owner.
    :param model: Active YggdrasilModel.
    :return: QuerySet ordered by name.
    """
    return BrowseView.objects.filter(model=model, owner=user).order_by("name")


def resolve_view_for_load(
    user: User,
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


def get_view(user: User, model: YggdrasilModel, slug: str) -> BrowseView:
    """
    Load a saved View by slug for the given owner and Model.

    :param user: View owner.
    :param model: Active YggdrasilModel.
    :param slug: URL-safe View slug. Example: ``"tech-only"``.
    :return: Matching BrowseView.
    :raises BrowseView.DoesNotExist: When no row matches.
    """
    return BrowseView.objects.get(model=model, owner=user, slug=slug)


def delete_view(user: User, model: YggdrasilModel, slug: str) -> None:
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
    params = _filter_params_from_payload(payload)
    _append_content_params(params, payload)
    logger.info(
        "BrowseViewService.expand_to_query_params | exit | slug=%s depth=%s mode=%s",
        view.slug,
        params["depth"][0],
        params["mode"][0],
    )
    return params


def _validated_view_name(user: User, model: YggdrasilModel, name: str) -> str:
    """Return trimmed View name or raise when blank."""
    cleaned_name = (name or "").strip()
    if not cleaned_name:
        logger.info(
            "BrowseViewService.save_view | validation | user_pk=%s model_slug=%s reason=empty_name",
            user.pk,
            model.slug,
        )
        raise ValidationError({"name": "View name is required."})
    return cleaned_name


def _reject_duplicate_slug(
    user: User,
    model: YggdrasilModel,
    slug: str,
    cleaned_name: str,
) -> None:
    """Raise when the owner already saved a View with the same slug."""
    if BrowseView.objects.filter(model=model, owner=user, slug=slug).exists():
        logger.info(
            "BrowseViewService.save_view | validation | user_pk=%s model_slug=%s reason=duplicate_slug slug=%s",
            user.pk,
            model.slug,
            slug,
        )
        raise ValidationError({"slug": f"A View named '{cleaned_name}' already exists."})


def _normalize_filters(filters: Any) -> dict[str, list[str]]:
    """Validate and normalize payload filter lists."""
    if not isinstance(filters, dict):
        raise ValidationError({"filters": "filters must be an object."})
    return {
        "packages": _coerce_str_list(filters.get("packages")),
        "element_stereotypes": _coerce_str_list(filters.get("element_stereotypes")),
        "relationship_stereotypes": _coerce_str_list(filters.get("relationship_stereotypes")),
    }


def _normalize_levels(levels: Any) -> dict[str, int]:
    """Validate and normalize payload depth."""
    if not isinstance(levels, dict):
        raise ValidationError({"levels": "levels must be an object."})
    try:
        depth = int(levels.get("depth", 1))
    except (TypeError, ValueError) as exc:
        raise ValidationError({"levels.depth": "depth must be an integer."}) from exc
    if depth < 1:
        raise ValidationError({"levels.depth": "depth must be >= 1."})
    return {"depth": depth}


def _normalize_presentation(presentation: Any) -> str:
    """Validate presentation mode."""
    if presentation not in VALID_PRESENTATIONS:
        raise ValidationError({"presentation": f"Must be one of {sorted(VALID_PRESENTATIONS)}."})
    return str(presentation)


def _attach_optional_payload_sections(payload: dict[str, Any], normalized: dict[str, Any]) -> None:
    """Merge optional content.field_map and viewport into normalized payload."""
    content = payload.get("content")
    if isinstance(content, dict):
        field_map = content.get("field_map")
        if isinstance(field_map, dict):
            normalized["content"] = {
                "field_map": {
                    str(slug): _coerce_str_list(paths)
                    for slug, paths in field_map.items()
                    if isinstance(paths, list)
                }
            }
        else:
            normalized["content"] = content
    if "viewport" in payload and payload["viewport"] is not None:
        normalized["viewport"] = payload["viewport"]


def _filter_params_from_payload(payload: dict[str, Any]) -> dict[str, list[str]]:
    """Map core filter and presentation fields to query param lists."""
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
    return params


def _append_content_params(params: dict[str, list[str]], payload: dict[str, Any]) -> None:
    """Append field_map and viewport query params when present."""
    content = payload.get("content") or {}
    field_map = content.get("field_map") or {}
    if isinstance(field_map, dict):
        for stereotype, paths in field_map.items():
            if paths:
                params[f"field_{stereotype}"] = list(paths)
    viewport = payload.get("viewport")
    if viewport is not None:
        params["viewport"] = [json.dumps(viewport)]


def _coerce_str_list(raw: Any) -> list[str]:
    """Normalize filter list values to non-empty strings."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValidationError({"filters": "Filter lists must be arrays."})
    return [str(item).strip() for item in raw if str(item).strip()]
