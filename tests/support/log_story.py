"""Assert Log Story Script beats in captured pytest logs."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def assert_log_story(
    caplog,
    *,
    where: str,
    beats: Mapping[str, Sequence[str]],
    level: str = "INFO",
) -> None:
    """
    Assert each beat has a matching log record for ``where``.

    :param caplog: pytest ``caplog`` fixture.
    :param where: Class.method substring that must appear in the message.
    :param beats: beat name → required substrings (all must appear in one record).
    :param level: minimum level name (INFO default).
    :raises AssertionError: naming the missing beat or substring.
    """
    min_level = getattr(logging, level.upper(), logging.INFO)
    records = [
        record
        for record in caplog.records
        if record.levelno >= min_level and where in record.getMessage()
    ]
    messages = [record.getMessage() for record in records]
    for beat, needles in beats.items():
        matched = [message for message in messages if all(needle in message for needle in needles)]
        if not matched:
            raise AssertionError(
                f"log story missing beat={beat!r} where={where!r} "
                f"needles={list(needles)!r}; saw={messages!r}"
            )
