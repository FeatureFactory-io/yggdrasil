# ACT-1-DISC-07 — Missing token fails with clear error

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-CLI-06 (same behavior)
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-07 Missing token fails with clear error
  When Priya runs:
    """
    ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4
    """
  Then the exit code is not 0
  And the output contains "token"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 30–35 | `_require_token` |
| `docs/plans/bootstrap-mvp/03-cli-bootstrap/ACT-1-CLI-06.md` | all | Canonical CLI plan — share tests |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- §18.5 Auth

---

## Current State Assessment

Duplicate of CLI-06 at implementation layer — one test module, two behave scenarios.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| Reuse `test_cli_bootstrap_missing_token` | unit | discovery feature tag |

---

## Logs to Emit

Same as ACT-1-CLI-06.

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Point discovery behave scenario to shared CLI test.
2. No duplicate logic.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_cli_bootstrap_missing_token -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya runs:` (multiline, no token) | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
