# ACT-1-DISC-12 — Empty repo after ignores yields nothing to scan

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-12 Empty repo after ignores yields nothing to scan
  Given ... fixture repository "empty_repo" is available
  ...
  Then the exit code is 0
  And the output contains "nothing to scan"
  And there are no orphan Elements without a ChangeSetItem
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `tests/fixtures/repos/empty_repo/` | all | Fixture with only gitignore |
| `ratatosk/discovery/runner.py` | tree | Early exit when scannable files = 0 |

---

## Do Not Do

Inherit SHARED-CONTRACT — success with empty plan, not error.

---

## SAO.md Sections That Apply

- §17.3 empty scan outcome

---

## Current State Assessment

empty_repo fixture may need creation; ignore rules must exclude all content.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc12_empty_repo_nothing_to_scan` | integration | message + exit 0 |
| `test_disc12_no_orphans` | integration | orphan invariant |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| tree walk | empty | scannable_file_count=0, reason=nothing_to_scan |

---

## MCP Tools to Expose

Not applicable or allow_empty propose.

---

## Implementation Steps

1. Add empty_repo fixture.
2. Detect zero scannable files after ignore filter.
3. Print `nothing to scan`, exit 0.
4. Skip handoff or allow_empty propose.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc12_empty_repo_nothing_to_scan -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the fixture repository "empty_repo" is available` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
