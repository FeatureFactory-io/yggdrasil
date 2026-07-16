"""
behave-django environment hooks for End-to-End (E2E) tests.

Run via: ``make test-e2e`` (``manage.py behave tests/e2e/``).

Uses behave-django's default ``BehaviorDrivenTestRunner``, which attaches a
``StaticLiveServerTestCase`` to ``context.test`` for every scenario — this
starts a real Django live server thread so Playwright can drive a genuine
browser against it. Isolation is flush-based (``TransactionTestCase``), not
atomic savepoints, because the live server runs in a separate thread with
its own DB connection.

Screenshots are captured after every step for visual audit trail (SAO.md
§5: "Takes screenshots for visual verification").
"""

import logging
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = Path("test-results/e2e")

# E2E steps resolve locally; shared page registry lives in docs/features/support/
_E2E_ROOT = Path(__file__).resolve().parent
_FEATURES_ROOT = Path(__file__).resolve().parents[2] / "docs" / "features"
if str(_E2E_ROOT) not in sys.path:
    sys.path.insert(0, str(_E2E_ROOT))
if str(_FEATURES_ROOT) not in sys.path:
    sys.path.insert(0, str(_FEATURES_ROOT))


def before_all(context):
    """Start one Playwright/Chromium instance for the whole E2E suite."""
    # Playwright's sync API may leave an async loop active; allow Django DB
    # teardown (flush) to run synchronously during behave-django hooks.
    os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    context.playwright = sync_playwright().start()
    context.browser = context.playwright.chromium.launch(headless=True)
    logger.info("E2E suite starting: browser=chromium headless=True")


def before_scenario(context, scenario):
    """Open a fresh browser page per scenario for full isolation."""
    context.page = context.browser.new_page()
    logger.info("E2E scenario starting: %s", scenario.name)


def after_step(context, step):
    """Screenshot after every step — filename is scenario+step, sanitized."""
    safe_scenario = re.sub(r"[^\w-]+", "_", context.scenario.name)
    safe_step = re.sub(r"[^\w-]+", "_", step.name)
    path = SCREENSHOT_DIR / f"{safe_scenario}__{safe_step}.png"
    context.page.screenshot(path=str(path))
    logger.info("E2E step screenshot saved: %s", path)


def after_scenario(context, scenario):
    """Close the page; DB flush/rollback is handled by behave-django."""
    context.page.close()
    logger.info("E2E scenario finished: %s status=%s", scenario.name, scenario.status.name)


def after_all(context):
    """Tear down the shared browser and Playwright process."""
    if hasattr(context, "browser"):
        context.browser.close()
    if hasattr(context, "playwright"):
        context.playwright.stop()
    logger.info("E2E suite finished")
