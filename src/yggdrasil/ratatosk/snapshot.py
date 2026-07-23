"""
Model snapshot port for Ratatosk discovery (step 1 of the unified loop).

Production CLI uses MCP (``McpSnapshotPort``). Pytest / in-process ATs inject
``LocalOrmSnapshotPort`` or a fake. Agent code never bypasses this port for
existing-model reads.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from yggdrasil.graph.models import Element, Relationship, YggdrasilModel

logger = logging.getLogger("yggdrasil.ratatosk.snapshot")


@runtime_checkable
class SnapshotPort(Protocol):
    """Fetch current model graph state before discovery analysis."""

    def fetch_model(self, model_slug: str) -> dict[str, Any]:
        """
        Return elements, relationships, and counts for ``model_slug``.

        :param model_slug: Model slug. Example: ``"yggdrasil"``.
        :return: Dict with keys ``elements``, ``relationships``,
            ``element_count``, ``relationship_count``, ``by_slug``.
        :raises RuntimeError: If the snapshot backend is unreachable or unauthorized.
        """
        ...


def normalize_snapshot(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Normalize element/relationship lists into the agent snapshot shape.

    :param elements: Element summary dicts (must include ``slug`` when present).
    :param relationships: Relationship summary dicts.
    :return: Snapshot dict with counts and ``by_slug`` index.
    """
    by_slug = {item["slug"]: item for item in elements if item.get("slug")}
    return {
        "elements": elements,
        "relationships": relationships,
        "element_count": len(elements),
        "relationship_count": len(relationships),
        "by_slug": by_slug,
    }


class LocalOrmSnapshotPort:
    """
    In-process ORM snapshot for pytest and behave ATs.

    Still surfaced to users/logs as an MCP-shaped fetch (journey string is
    printed by the agent, not by this port).
    """

    def fetch_model(self, model_slug: str) -> dict[str, Any]:
        """Load elements and relationships from the local database."""
        try:
            model = YggdrasilModel.objects.get(slug__iexact=model_slug)
        except YggdrasilModel.DoesNotExist:
            try:
                model = YggdrasilModel.objects.get(name__iexact=model_slug)
            except YggdrasilModel.DoesNotExist as exc:
                msg = f"Model not found for snapshot: {model_slug!r}"
                raise RuntimeError(msg) from exc
        elements = list(
            Element.objects.filter(model=model).values(
                "id", "name", "slug", "owner", "stereotype__name", "package__name"
            )
        )
        relationships = list(
            Relationship.objects.filter(model=model).values(
                "id", "source_id", "target_id", "stereotype__slug"
            )
        )
        logger.info(
            "LocalOrmSnapshotPort.fetch_model | model=%s elements=%s relationships=%s",
            model.slug,
            len(elements),
            len(relationships),
        )
        return normalize_snapshot(elements, relationships)


class McpSnapshotPort:
    """Snapshot via Ratatosk MCP client (``list_elements`` + relationships)."""

    def __init__(self, client: Any) -> None:
        """
        :param client: Object with ``call_tool(name, arguments) -> dict``.
        """
        self._client = client

    def fetch_model(self, model_slug: str) -> dict[str, Any]:
        """
        Fetch model state through MCP tools.

        :param model_slug: Target model slug.
        :raises RuntimeError: On MCP/HTTP failure (no ORM fallback).
        """
        logger.info("McpSnapshotPort.fetch_model | model=%s via MCP", model_slug)
        try:
            elements_page = self._client.call_tool(
                "list_elements",
                {"model": model_slug, "limit": 200, "offset": 0},
            )
            rel_page = self._client.call_tool(
                "list_relationships",
                {"model": model_slug, "limit": 200},
            )
            relationships = list(rel_page.get("items") or [])
        except Exception as exc:
            msg = f"MCP snapshot failed for model {model_slug!r}: {exc}"
            logger.error("McpSnapshotPort.fetch_model | %s", msg)
            raise RuntimeError(msg) from exc

        raw_items = list(elements_page.get("items") or [])
        elements = [_mcp_element_to_snapshot(item) for item in raw_items]
        total = int(elements_page.get("total") or len(elements))
        # Paginate if needed (cap at 1000 for one run).
        offset = len(elements)
        while offset < total and offset < 1000:
            page = self._client.call_tool(
                "list_elements",
                {"model": model_slug, "limit": 200, "offset": offset},
            )
            batch = [_mcp_element_to_snapshot(item) for item in (page.get("items") or [])]
            if not batch:
                break
            elements.extend(batch)
            offset = len(elements)

        snapshot = normalize_snapshot(elements, relationships)
        # Prefer server total when present.
        if total:
            snapshot["element_count"] = total
        logger.info(
            "McpSnapshotPort.fetch_model | model=%s elements=%s relationships=%s",
            model_slug,
            snapshot["element_count"],
            snapshot["relationship_count"],
        )
        return snapshot


def _mcp_element_to_snapshot(item: dict[str, Any]) -> dict[str, Any]:
    """Map MCP element summary into agent snapshot element dict."""
    name = str(item.get("name") or "")
    slug = str(item.get("slug") or name).lower().replace(" ", "-")
    stereotype = item.get("stereotype") or item.get("stereotype_name") or ""
    package = item.get("package") or item.get("package_name") or ""
    if isinstance(stereotype, dict):
        stereotype = stereotype.get("name") or stereotype.get("slug") or ""
    if isinstance(package, dict):
        package = package.get("name") or package.get("slug") or ""
    return {
        "id": item.get("id"),
        "name": name,
        "slug": slug,
        "owner": item.get("owner") or "",
        "stereotype__name": stereotype,
        "package__name": package,
    }
