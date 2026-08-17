# Activity: Fix Bug

**Activity ID**: 203
**Order**: 9
**Phase**: Construction
**Dependencies**: Predecessor: Activity 103 (Process Change Request)

## Description

Fix Bug

## Guidance

## Purpose
Fix a reported defect using a test-first workflow: prove the bug with a failing test, implement the fix, prove green, run full regression, then gate integration/PR/hotfix decisions with the user.

This activity implements code. It does **not** reconcile requirements — use Process Change Request (#103) for scope or spec changes.

## Prerequisites

- A **Bug Report** (GitHub Issue) filed via `report_bug` MCP tool or the Feedback UI
- Bug may have been filed during Check Definition of Done (#101), Finalize Feature (#102), or Acceptance, Bug Reports & Deploy Fixes (#183)

## Steps

### 1. Analyze Why Tests Missed the Bug

- Read the Bug Report thoroughly (Description, Reproduction, Environment, severity if present)
- Identify affected feature files, scenarios, Screen IDs, and code paths
- Determine **why existing tests did not catch the defect** — missing scenario, weak assertion, wrong test layer, integration gap, flaky test, etc.
- Document the gap briefly (issue comment or working notes)

### 2. Add or Extend Tests (Red)

- Write or extend tests that **reproduce the bug** — they must fail before the fix
- Prefer the lowest appropriate layer per SAO Test Strategy: unit → integration → AT (`docs/features/`) → E2E (`tests/e2e/`)
- Follow `do-test-first` and `do-not-mock-in-integration-tests`
- Run the new or extended test(s) and confirm they fail for the expected reason

### 3. Implement the Fix

- Implement the minimal correct fix
- Keep scope focused — no unrelated refactors

### 4. Prove the Fix (Green)

- Run the new or extended test(s) — must pass
- If UI or journey behavior changed, re-run relevant BPE-04 / BPE-05 checkpoints for the affected scenario

### 5. Full Regression

- Run the full test suite: `pytest tests/`
- Run E2E suite when UI or journey paths changed: `pytest tests/e2e/`
- **100% pass rate required** before closing — same standard as Finalize Feature (#102)

### 6. Commit and User Gate

- Commit with Angular convention:
  ```bash
  git add -A
  git commit -m "fix({scope}): {bug title}"
  ```
- Ask the user:
  1. **Integrate or submit PR?** — merge to main locally, or open / submit a pull request?
  2. **Hotfix deployment needed?** — if production is affected, coordinate a patch release per MIN-06 / deployment playbook
- Do **not** push until the user approves

## Rules to Follow

Before fixing, **read** each Rule below in this playbook (by slug), then **apply** it:

- `do-test-first`
- `do-not-mock-in-integration-tests`
- `do-follow-commit-convention`
- `do-small-increments`
- `do-informative-logging` (when the fix touches decision points)

## Success Criteria

- Root cause of the test gap identified and documented
- Failing test proves the bug before the fix
- Fix implemented; proving tests pass
- Full regression green (100% pass rate)
- Commit made; user decision recorded on integrate / PR / hotfix

## Inputs

Read these before starting this activity.

- **Bug Report** (Document, Required) — produced by Check Definition of Done (#101), Finalize Feature (#102), or Acceptance, Bug Reports & Deploy Fixes (#183) via `report_bug` MCP tool or Feedback UI.

## Agent

**Name**: Dr. Dobbs v2
**Description**: # Cautious Developer Agent Guide

**Motto**: "Code that's easy to prove correct is code that works"

## Skill

None

## Rules

- **Test First** (`do-test-first`)
- **Do Not Mock In Integration Tests** (`do-not-mock-in-integration-tests`)
- **Follow Commit Convention** (`do-follow-commit-convention`)
- **Small Increments** (`do-small-increments`)
- **Informative Logging** (`do-informative-logging`)

## Artifacts Produced

None

## Artifacts Consumed

- **Bug Report** (Document) - Required

## Notes

No additional notes.
