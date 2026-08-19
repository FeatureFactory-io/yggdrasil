"""Request-scoped log correlation (SAO §11).

Binds ``request_id`` (and related HTTP fields) onto structlog contextvars and
every stdlib ``LogRecord`` so console, ``logs/app.log``, and pytest ``caplog``
can reconstruct a single request.
"""

from __future__ import annotations

import logging
from typing import Any

import structlog

_FACTORY_INSTALLED = False
# Only copy correlation ids onto LogRecord. Binding HTTP ``path``/``method``
# onto the record collides with stdlib ``extra={"path": ...}`` (KeyError).
_RECORD_CONTEXT_KEYS = ("request_id", "user_id")
_CONSOLE_DROP_KEYS = (
    "context",
    "file",
    "thread",
    "line",
    "module",
    "code_module",
    "code_line",
    "code_thread",
    "method",
    "path",
    "user_id",
)


def bind_request_context(**values: Any) -> None:
    """
    Bind request-scoped fields for the current task/thread.

    :param values: Correlation fields. Example: ``request_id="req-7f3a"``.
    """
    structlog.contextvars.bind_contextvars(**values)


def clear_request_context() -> None:
    """Clear request-scoped fields so the next request cannot inherit them."""
    structlog.contextvars.clear_contextvars()


def install_log_record_factory() -> None:
    """
    Copy contextvars onto every stdlib ``LogRecord``.

    Safe to call more than once; subsequent calls are no-ops.
    """
    global _FACTORY_INSTALLED
    if _FACTORY_INSTALLED:
        return
    previous_factory = logging.getLogRecordFactory()

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous_factory(*args, **kwargs)
        _copy_contextvars_onto_record(record)
        return record

    logging.setLogRecordFactory(factory)
    _FACTORY_INSTALLED = True


def _copy_contextvars_onto_record(record: logging.LogRecord) -> None:
    """Attach correlation ids from contextvars without clobbering extra fields."""
    context = structlog.contextvars.get_contextvars()
    for key in _RECORD_CONTEXT_KEYS:
        if key in context:
            setattr(record, key, context[key])


def add_stdlib_callsite(
    _logger: logging.Logger, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Copy stdlib callsite fields onto the structlog event for JSON stories.

    :param event_dict: Formatter event, may include ``_record``.
    :return: Event with ``module``, ``line``, ``thread`` when missing.
    """
    record = event_dict.get("_record")
    if record is None:
        return event_dict
    event_dict.setdefault("module", record.name)
    event_dict.setdefault("line", record.lineno)
    event_dict.setdefault("thread", record.threadName)
    event_dict.setdefault("file", record.filename)
    if getattr(record, "context", None) is not None:
        event_dict.setdefault("context", record.context)
    return event_dict


def omit_console_context_fields(
    _logger: logging.Logger, _method: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """
    Keep the terminal line short; full context lives in ``logs/app.log``.

    :param event_dict: Console formatter event.
    :return: Event without bulky story fields.
    """
    for key in _CONSOLE_DROP_KEYS:
        event_dict.pop(key, None)
    return event_dict
