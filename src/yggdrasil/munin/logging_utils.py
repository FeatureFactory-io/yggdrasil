"""Structured INFO logging helpers for Munin (do-informative-logging.mdc)."""

from __future__ import annotations

import io
import logging
from pprint import pformat
from typing import Any

logger = logging.getLogger("yggdrasil.munin.logging")

_BUFFER = io.StringIO()


def log_munin_entry(
    operation: str,
    *,
    where: str,
    user_id: int | None = None,
    model_id: int | None = None,
    llm_model: str = "",
    **context: Any,
) -> None:
    """
    Log method entry with who/what/where per do-informative-logging.

    :param operation: Human-readable operation name.
    :param where: Module-qualified location (class.method).
    :param user_id: Authenticated user PK when known.
    :param model_id: YggdrasilModel PK when known.
    :param llm_model: Resolved Munin LLM model id.
    :param context: Additional key=value audit fields.
    """
    logger.info(
        "Munin.entry | operation=%s where=%s user_id=%s model_id=%s llm_model=%s context=%s",
        operation,
        where,
        user_id,
        model_id,
        llm_model or "(unset)",
        context,
    )


def log_munin_structure(label: str, payload: Any) -> None:
    """
    Dump a structure to app.log using ``pformat`` (rule §Structures).

    :param label: Dataset name for grep (e.g. ``element_ops``).
    :param payload: Dict/list/set to serialize.
    """
    logger.info(
        "Munin.structure | label=%s\n%s", label, pformat(payload, width=120, sort_dicts=True)
    )


def log_munin_llm_request(
    *,
    where: str,
    user_id: int | None,
    llm_model: str,
    system: str,
    prompt: str,
    element_count: int = 0,
) -> None:
    """
    Log complete Munin LLM request — system + user prompt at INFO.

    :param where: Caller location.
    :param user_id: Requesting user PK.
    :param llm_model: Model id string.
    :param system: System prompt text.
    :param prompt: User prompt text.
    :param element_count: Number of elements in the request.
    """
    logger.info(
        "Munin.llm_request | where=%s user_id=%s llm_model=%s element_count=%s "
        "system_chars=%s prompt_chars=%s",
        where,
        user_id,
        llm_model,
        element_count,
        len(system),
        len(prompt),
    )
    logger.info("Munin.llm_request.system | where=%s\n%s", where, system)
    logger.info("Munin.llm_request.prompt | where=%s\n%s", where, prompt)


def log_munin_llm_response(
    *,
    where: str,
    user_id: int | None,
    llm_model: str,
    raw_content: str,
    parsed_count: int,
    accepted_count: int,
    rejected_count: int,
) -> None:
    """
    Log complete Munin LLM response and parse outcome.

    :param where: Caller location.
    :param user_id: Requesting user PK.
    :param llm_model: Model id string.
    :param raw_content: Full LLM response text.
    :param parsed_count: Relationship candidates parsed from JSON.
    :param accepted_count: Ops accepted after validation.
    :param rejected_count: Ops rejected (unknown names, malformed).
    """
    logger.info(
        "Munin.llm_response | where=%s user_id=%s llm_model=%s response_chars=%s "
        "parsed=%s accepted=%s rejected=%s",
        where,
        user_id,
        llm_model,
        len(raw_content or ""),
        parsed_count,
        accepted_count,
        rejected_count,
    )
    logger.info("Munin.llm_response.content | where=%s\n%s", where, raw_content or "")


def log_munin_branch(
    *,
    where: str,
    branch: str,
    reason: str,
    user_id: int | None = None,
    **outcome: Any,
) -> None:
    """
    Log conditional branch decision with explicit why (rule §Branches).

    :param where: Caller location.
    :param branch: Branch name taken.
    :param reason: Why this branch was chosen.
    :param user_id: Requesting user PK.
    :param outcome: Result fields (counts, source tags, etc.).
    """
    logger.info(
        "Munin.branch | where=%s branch=%s reason=%s user_id=%s outcome=%s",
        where,
        branch,
        reason,
        user_id,
        outcome,
    )


def log_munin_exit(
    operation: str,
    *,
    where: str,
    user_id: int | None = None,
    success: bool = True,
    **result: Any,
) -> None:
    """
    Log method exit with result summary.

    :param operation: Operation name matching entry.
    :param where: Module-qualified location.
    :param user_id: Requesting user PK.
    :param success: Whether the operation succeeded.
    :param result: Outcome key=value pairs.
    """
    level = logging.INFO if success else logging.ERROR
    logger.log(
        level,
        "Munin.exit | operation=%s where=%s user_id=%s success=%s result=%s",
        operation,
        where,
        user_id,
        success,
        result,
    )


def log_munin_error(
    operation: str,
    *,
    where: str,
    error: Exception | str,
    user_id: int | None = None,
    **context: Any,
) -> None:
    """
    Log failure with full context for root-cause diagnosis (rule §Errors).

    :param operation: Operation that failed.
    :param where: Caller location.
    :param error: Exception or message.
    :param user_id: Requesting user PK.
    :param context: State at failure time.
    """
    logger.error(
        "Munin.error | operation=%s where=%s user_id=%s error=%s context=%s",
        operation,
        where,
        user_id,
        error,
        context,
    )
