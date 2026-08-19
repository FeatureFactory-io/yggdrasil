"""Request-scoped execution ray across Yggdrasil layers.

When ``REQUEST_TRACE`` is on, every Yggdrasil Python call/return during an
HTTP request is logged as ``RequestTrace`` with ``depth`` and ``where``, bound
to the same ``request_id`` as the rest of the request.
"""

from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import FrameType

logger = logging.getLogger("yggdrasil.trace")

_busy: ContextVar[bool] = ContextVar("request_trace_busy", default=False)
_stack: ContextVar[list[float] | None] = ContextVar("request_trace_stack", default=None)

_SKIP_PREFIXES = (
    "yggdrasil.log_context",
    "yggdrasil.request_trace",
)
_SKIP_NAMES = frozenset(
    {
        "<lambda>",
        "<genexpr>",
        "<listcomp>",
        "<setcomp>",
        "<dictcomp>",
        "<module>",
    }
)


@contextmanager
def traced_request(*, enabled: bool | None = None) -> Iterator[None]:
    """
    Profile Yggdrasil frames on the current thread until the context exits.

    :param enabled: Override ``settings.REQUEST_TRACE``. Example: ``True``.
    """
    if not _resolve_enabled(enabled):
        yield
        return
    previous = sys.getprofile()
    stack_token = _stack.set([])
    sys.setprofile(_profile)
    try:
        yield
    finally:
        sys.setprofile(previous)
        _stack.reset(stack_token)


def _resolve_enabled(enabled: bool | None) -> bool:
    """Return whether the request ray should run."""
    if enabled is not None:
        return enabled
    return bool(getattr(settings, "REQUEST_TRACE", False))


def _profile(frame: FrameType, event: str, _arg: Any) -> None:
    """sys.setprofile hook — records yggdrasil call/return events."""
    if event not in {"call", "return"} or _busy.get():
        return
    stack = _stack.get()
    if stack is None or not _should_trace(frame):
        return
    busy_token = _busy.set(True)
    try:
        if event == "call":
            _log_entry(frame, stack)
        else:
            _log_exit(frame, stack)
    finally:
        _busy.reset(busy_token)


def _should_trace(frame: FrameType) -> bool:
    """Return True for Yggdrasil application frames that belong on the ray."""
    module = frame.f_globals.get("__name__", "") or ""
    if not module.startswith("yggdrasil"):
        return False
    if any(module == prefix or module.startswith(f"{prefix}.") for prefix in _SKIP_PREFIXES):
        return False
    name = frame.f_code.co_name
    return name not in _SKIP_NAMES and not name.startswith("__")


def _log_entry(frame: FrameType, stack: list[float]) -> None:
    """Push a frame and log RequestTrace entry."""
    depth = len(stack)
    stack.append(time.perf_counter())
    logger.info("RequestTrace | entry | depth=%s where=%s", depth, _where(frame))


def _log_exit(frame: FrameType, stack: list[float]) -> None:
    """Pop a frame and log RequestTrace exit with duration."""
    if not stack:
        return
    started = stack.pop()
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "RequestTrace | exit | depth=%s where=%s duration_ms=%.2f",
        len(stack),
        _where(frame),
        duration_ms,
    )


def _where(frame: FrameType) -> str:
    """
    Return module-qualified location.

    :param frame: Profiled Python frame.
    :return: Example: ``yggdrasil.web.views.ViewBrowseView.get``.
    """
    module = frame.f_globals.get("__name__", "") or ""
    qualname = getattr(frame.f_code, "co_qualname", frame.f_code.co_name)
    return f"{module}.{qualname}"
