# Activity: Bootstrap Test Harness

**Activity ID**: 188
**Order**: 2
**Phase**: Elaboration
**Dependencies**: Predecessor: Activity 187 (Define Test Architecture)

## Description

Bootstrap Test Harness

## Guidance

# Bootstrap Test Harness

## Objective

Set up the complete test infrastructure: directory structure, pytest configuration, behave-django configuration, Playwright integration, Makefile targets, and continuous test runner.

---

## Process

### 1. Create Test Directory Structure

```
tests/
├── unit/                    # pytest -m unit
│   └── conftest.py
├── integration/             # pytest -m integration
│   └── conftest.py
├── e2e/                     # behave + Playwright (E2E)
│   ├── *.feature            # @e2e tag
│   ├── steps/
│   └── environment.py
├── infra/                   # CDK assertion tests
├── fixtures/                # Shared fixture data
│   ├── seed.json
│   └── presets/
└── conftest.py

docs/features/               # BDD spec + AT runner (behave.ini paths = docs/features)
├── act-*/                   # .feature files per act
├── steps/                   # Step definitions (TFK Step Library)
├── support/                 # page registry
└── environment.py           # behave lifecycle hooks
```

### 2. Configure pytest

```ini
[pytest]
DJANGO_SETTINGS_MODULE = {project}.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
addopts =
    -v --strict-markers --tb=short
    --log-file=tests.log --log-file-level=INFO
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (real deps, no mocking)
    acceptance: Acceptance tests (behave BDD)
    e2e: End-to-end tests (Playwright, excluded from default runs)
    slow: Slow running tests
```

### 3. Configure behave

```ini
# behave.ini
[behave]
paths = docs/features
format = pretty
logging_level = INFO
tags = ~@wip
```

Create `docs/features/environment.py` and `tests/e2e/environment.py` with:
- `before_all`: Django setup, database connection, load session-level fixtures
- `before_scenario`: Transaction savepoint for test isolation
- `after_scenario`: Rollback to savepoint
- `after_all`: Cleanup

### 4. Configure Playwright Integration

For E2E tests using behave + Playwright with LiveServerTestCase.

## Agent

None

## Skill

**Title**: Behave-Django BDD Runner
**Capability Domain**: BDD Test Execution
**Technology Stack**: behave, django, behave-django

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
