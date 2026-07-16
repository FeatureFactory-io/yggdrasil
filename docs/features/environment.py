"""
behave-django environment hooks for Acceptance Tests (AT).

Run via: ``make test-at`` (``manage.py behave --simple docs/features/``).

The ``--simple`` flag selects behave-django's ``SimpleTestRunner``, which
attaches a ``DjangoSimpleTestCase`` (a ``django.test.TestCase`` subclass) to
``context.test`` for every scenario. ``TestCase`` wraps each test in
``transaction.atomic()`` and rolls back to the savepoint on teardown — this
gives AT scenarios per-scenario isolation with zero explicit transaction
code here. No live server / browser support (Django test client only),
which matches the AT contract: single screen/feature, no browser overhead.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Ensure step/support imports resolve when behave loads docs/features/steps/*.py
_FEATURES_ROOT = Path(__file__).resolve().parent
if str(_FEATURES_ROOT) not in sys.path:
    sys.path.insert(0, str(_FEATURES_ROOT))


def before_all(context):
    """Register session-level seed fixtures, loaded fresh for every scenario.

    ``context.fixtures`` is read by behave-django's ``setup_fixtures`` hook
    and assigned to the ``TestCase.fixtures`` attribute, so Django's
    standard ``loaddata`` fixture loading applies automatically per
    scenario (inside the same atomic block that gets rolled back after).
    """
    context.fixtures = ["seed"]
    logger.info("AT suite starting: fixtures=%s", context.fixtures)


def before_scenario(context, scenario):
    """Log scenario start for traceability in tests.log."""
    logger.info("AT scenario starting: %s", scenario.name)


def after_scenario(context, scenario):
    """Log scenario outcome; DB rollback is handled by behave-django."""
    logger.info("AT scenario finished: %s status=%s", scenario.name, scenario.status.name)
