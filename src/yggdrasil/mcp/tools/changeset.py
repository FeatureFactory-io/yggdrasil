"""
MCP ChangeSet tools: approve_changeset, reject_changeset, do_other_changeset
(SAO.md §18.3 — tool inventory, ChangeSet review tools).

These are the headless equivalents of the GUI ChangeSet review screen.
Auth: user_id injected server-side — never from tool args.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("yggdrasil.mcp.tools.changeset")


def approve_changeset(
    id: int,
    item_ids: list[int] | None = None,
) -> dict:
    """
    Apply all (or specified) pending operations in a ChangeSet.

    :param id: ChangeSet PK. Example: 1
    :param item_ids: Specific ChangeSetItem PKs to apply.
        None = apply all pending. Example: [1, 2]
    :return: {"changeset_id": N, "applied_count": N, "status": "applied"|"pending"}
    :raises PermissionError: If current user lacks write access.
    :raises ValueError: If ChangeSet not found or already applied.
    """
    raise NotImplementedError()


def reject_changeset(
    id: int,
    item_ids: list[int] | None = None,
    reason: str = "",
) -> dict:
    """
    Reject all (or specified) pending operations; optionally learn from reason.

    When reason is provided, a MuninRule is created so Munin avoids this
    pattern in future runs (SAO.md §17.5 — Learning module).

    :param id: ChangeSet PK. Example: 1
    :param item_ids: Specific ChangeSetItem PKs to reject. None = reject all.
    :param reason: Rejection reason. Example:
        "Code diagram is for repository structure, not runtime services"
    :return: {"changeset_id": N, "rejected_count": N, "rule_created": bool}
    :raises PermissionError: If current user lacks write access.
    :raises ValueError: If ChangeSet not found.
    """
    raise NotImplementedError()


def do_other_changeset(
    id: int,
    item_ids: list[int],
    instructions: str,
) -> dict:
    """
    Reject specified items and queue Munin to re-plan them with instructions.

    Instructions are appended to LEARNED (MuninRule) for future reference.
    Munin re-processes asynchronously; the response returns the original
    ChangeSet ID and the queued re-plan task ID.

    :param id: ChangeSet PK. Example: 1
    :param item_ids: ChangeSetItem PKs to re-plan. Example: [3]
    :param instructions: Guidance for Munin's re-plan. Example:
        "don't add this to the Container diagram, it's an external system"
    :return: {"changeset_id": N, "redirected_count": N, "replan_task_id": "..."}
    :raises PermissionError: If read-only scope.
    :raises ValueError: If item_ids is empty or ChangeSet not found.
    """
    raise NotImplementedError()


def ask_munin(question: str, model: str | None = None) -> dict:
    """
    Ask Munin a natural-language question about the architecture graph.

    Munin has access to the full graph via query tools. Returns a structured
    response with cited element references and optional navigation hints.

    :param question: Natural language query. Example:
        "What domain objects have changed since Jan?"
    :param model: Model slug to scope the question. Example: "yggdrasil"
    :return: {"answer": "...", "cited_elements": [...], "navigation_url": "..."|None}
    :raises PermissionError: If current user has no read access.
    """
    raise NotImplementedError()
