#!/usr/bin/env python
"""
Continuous test runner (``do-continuous-testing.mdc``).

Watches ``src/`` and ``features/`` for ``.py`` / ``.feature`` changes and
re-runs the unit + integration pytest suite on every change, debounced to
avoid re-running mid-save. Output is written to ``tests.log`` (via pytest's
own ``--log-file``, configured in ``pyproject.toml``) plus echoed to stdout.

Usage::

    make watch
    # or directly:
    python continuous_test_runner.py
"""

from __future__ import annotations

import logging
import subprocess
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger("yggdrasil.continuous_test_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

WATCH_PATHS = ["src", "features", "tests"]
DEBOUNCE_SECONDS = 1.0
RELEVANT_SUFFIXES = {".py", ".feature"}


class _DebouncedTestRunHandler(FileSystemEventHandler):
    """Re-runs pytest on relevant file changes, collapsing rapid bursts."""

    def __init__(self) -> None:
        self._last_run_at: float = 0.0

    def on_modified(self, event: FileSystemEvent) -> None:
        self._maybe_run(event)

    def on_created(self, event: FileSystemEvent) -> None:
        self._maybe_run(event)

    def _maybe_run(self, event: FileSystemEvent) -> None:
        """Trigger a debounced pytest run if the changed file is relevant.

        :param event: filesystem event from watchdog.
        """
        src_path = event.src_path.decode() if isinstance(event.src_path, bytes) else event.src_path
        if event.is_directory or Path(src_path).suffix not in RELEVANT_SUFFIXES:
            return
        now = time.monotonic()
        if now - self._last_run_at < DEBOUNCE_SECONDS:
            return
        self._last_run_at = now
        logger.info("Change detected: %s — re-running tests", src_path)
        _run_pytest()


def _run_pytest() -> None:
    """Run the unit + integration suite; result is also written to tests.log."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short"],
        check=False,
    )
    status = "PASSED" if result.returncode == 0 else "FAILED"
    logger.info("Test run %s (exit_code=%s) — see tests.log for detail", status, result.returncode)


def main() -> None:
    """Start the watcher loop; runs the full suite once immediately, then on change."""
    logger.info("Continuous test runner starting — watching %s", WATCH_PATHS)
    _run_pytest()

    observer = Observer()
    handler = _DebouncedTestRunHandler()
    for path in WATCH_PATHS:
        if Path(path).exists():
            observer.schedule(handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Continuous test runner stopping")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
