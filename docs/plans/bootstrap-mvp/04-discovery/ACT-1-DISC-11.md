# ACT-1-DISC-11 — Missing repo path fails with clear error

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-11 Missing repo path fails with clear error
  ...
  When Priya runs ratatosk bootstrap /tmp/yggdrasil-no-such-repo-xyz ...
  Then the exit code is not 0
  And the output contains "path"
  And no ChangeSet with source "ratatosk" was created for this run
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | path validation | Before MCP / scan |
| `ratatosk/discovery/runner.py` | exists check | Early exit |

---

## Do Not Do

Inherit SHARED-CONTRACT — no handoff on bad path.

---

## SAO.md Sections That Apply

- Defensive input validation at CLI boundary

---

## Current State Assessment

Click `exists=False` on path arg — validation must happen in command body.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc11_missing_repo_path` | unit Click | exit ≠ 0, path in message |
| `test_disc11_no_changeset_on_bad_path` | integration | no ChangeSet |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| cli bootstrap | path invalid | repo_path, reason=not_found |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Validate path.is_dir() before runner.
2. Red tests.
3. User-friendly message with `path` substring.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_disc11_missing_repo_path -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `And the output contains "path"` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
