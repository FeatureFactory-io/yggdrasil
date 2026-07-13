# Activity: Build Step Library

**Activity ID**: 189
**Order**: 3
**Phase**: Elaboration
**Dependencies**: Predecessor: Activity 188 (Bootstrap Test Harness)

## Description

Build Step Library

## Guidance

# Build Step Library

## Objective

Create a reusable library of Gherkin step definitions that ESM can compose scenarios from. The library grows over time — initial seed covers generic patterns, project-specific steps are added via TAF-07 as needed.

---

## Process

### 1. Organize Steps by Domain

```
tests/acceptance/features/steps/
├── navigation_steps.py      # Page navigation, URL verification
├── form_steps.py            # Form filling, submission, validation
├── table_steps.py           # Table rendering, sorting, filtering
├── auth_steps.py            # Login, logout, permissions
├── assertion_steps.py       # Generic assertions (visible, contains, count)
├── dialog_steps.py          # Modal/dialog interactions
├── common_steps.py          # Wait, screenshot, context helpers
└── __init__.py
```

### 2. Generic Step Patterns

**Navigation:**
- `Given {user} is on the "{page_name}" page`
- `When {user} navigates to "{url}"`
- `Then {user} should see the "{page_name}" page`

**Forms:**
- `When {user} enters "{value}" into "{field}"`
- `When {user} selects "{option}" from "{dropdown}"`
- `When {user} clicks "{button}"`
- `When {user} submits the form`

**Tables:**
- `Then {user} sees table "{table_name}" with {n} rows`
- `Then the table "{table_name}" should contain "{text}"`
- `When {user} sorts table "{table_name}" by "{column}"`

**Auth:**
- `Given {user} is logged in as "{role}"`
- `Given {user} is not authenticated`

**Assertions:**
- `Then {user} should see "{text}"`
- `Then {user} should not see "{text}"`
- `Then the element "{test_id}" should be visible`

### 3. Step Implementation Conventions

- All steps use `data-testid` selectors for element targeting
- Parameterize generically — avoid hardcoding entity names
- Log actions at INFO level
- Add module-level docstring listing all steps

## Agent

None

## Skill

**Title**: Behave-Django BDD Runner
**Capability Domain**: BDD Test Execution
**Technology Stack**: behave, django, behave-django

**Title**: Gherkin Step Library Patterns
**Capability Domain**: BDD Step Engineering
**Technology Stack**: gherkin, behave, step-definitions

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
