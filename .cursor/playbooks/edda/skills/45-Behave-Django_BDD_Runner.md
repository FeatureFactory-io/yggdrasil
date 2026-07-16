# Behave-Django BDD Runner

**Skill ID**: 45
**Capability Domain**: BDD Test Execution
**Technology Stack**: behave, django, behave-django
**Linked Activities**: 2

## Content

# Skill: Behave-Django BDD Runner

**Capability Domain**: BDD_RUNNER
**Technology Stack**: behave+Django+Playwright

## Overview

Patterns for running BDD acceptance and E2E tests using behave-django with Playwright browser automation. Covers behave configuration, environment lifecycle, step definitions, LiveServerTestCase integration, and context passing.

## Reference Implementation

### Pattern 1: behave.ini Configuration

```ini
[behave]
paths = docs/features
format = pretty
logging_level = INFO
tags = ~@e2e
stdout_capture = false
stderr_capture = false
log_capture = false
```

### Pattern 2: environment.py Lifecycle (Acceptance Tests)

```python
# docs/features/environment.py
import django
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command

def before_all(context):
    django.setup()
    setup_test_environment()
    call_command('loaddata', 'tests/fixtures/seed.json')

def before_scenario(context, scenario):
    from django.test import TestCase
    context._test = TestCase('__init__')
    context._test._pre_setup()

def after_scenario(context, scenario):
    context._test._post_teardown()

def after_all(context):
    teardown_test_environment()
```

### Pattern 3: environment.py Lifecycle (E2E Tests with Playwright)

Uses Playwright browser, LiveServerTestCase, base_url targeting, and screenshot-on-step.
