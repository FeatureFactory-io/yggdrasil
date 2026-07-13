"""Graph services — traversal, changeset application."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import connection
from django.utils import timezone

from graph.models import ChangeSet, ChangeSetStatus, Element, Relationship


def traverse_from(
    element_id: int,
    depth: int = 3,
    as_of: datetime | None = None,
) -> list[dict[str, Any]]:
    """Recursive CTE traversal from an element (outgoing edges)."""
    as_of = as_of or timezone.now()
    sql = """
        WITH RECURSIVE walk AS (
            SELECT e.id, e.name, 0 AS hop
            FROM graph_element e
            WHERE e.id = %s
              AND e.valid_from <= %s
              AND (e.valid_to IS NULL OR e.valid_to > %s)
            UNION ALL
            SELECT e2.id, e2.name, w.hop + 1
            FROM graph_relationship r
            JOIN walk w ON r.from_element_id = w.id
            JOIN graph_element e2 ON r.to_element_id = e2.id
            WHERE w.hop < %s
              AND r.valid_from <= %s
              AND (r.valid_to IS NULL OR r.valid_to > %s)
              AND e2.valid_from <= %s
              AND (e2.valid_to IS NULL OR e2.valid_to > %s)
        )
        SELECT DISTINCT id, name, hop FROM walk ORDER BY hop, name;
    """
    params = [element_id, as_of, as_of, depth, as_of, as_of, as_of, as_of]
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def apply_changeset(changeset: ChangeSet, min_confidence: float = 0.8) -> int:
    """Apply high-confidence items from a changeset. Returns count applied."""
    applied = 0
    now = timezone.now()
    for item in changeset.items:
        if item.get("confidence", 0) < min_confidence:
            continue
        action = item.get("action")
        if action == "create_element":
            Element.objects.create(
                name=item["name"],
                stereotype_id=item["stereotype_id"],
                package_id=item.get("package_id"),
                properties=item.get("properties", {}),
                valid_from=now,
                source="ratatosk",
                ratatosk_run_id=changeset.run_id,
                confidence=item.get("confidence", 1.0),
            )
            applied += 1
        elif action == "create_relationship":
            Relationship.objects.create(
                from_element_id=item["from_element_id"],
                to_element_id=item["to_element_id"],
                stereotype_id=item["stereotype_id"],
                properties=item.get("properties", {}),
                valid_from=now,
                source="ratatosk",
                ratatosk_run_id=changeset.run_id,
                confidence=item.get("confidence", 1.0),
            )
            applied += 1
    changeset.status = (
        ChangeSetStatus.APPLIED if applied == len(changeset.items) else ChangeSetStatus.PARTIAL
    )
    changeset.save(update_fields=["status", "updated_at"])
    return applied
