# ACT-1-CLI-05 — High-confidence auto-apply; below-threshold queue for review

> **DEFER (Tier 4)** — Implement after W0–W9 green. Plan is complete for PIN handoff.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** MCP-PROPOSE-CHANGESET, ACT-5-MCP-CHANGESET-01
**Blocks:** —

---

## Scenario (Gherkin)

```gherkin
@wip
Scenario: ACT-1-CLI-05 High-confidence operations auto-apply; below-threshold ops queue for review
  Given a ChangeSet with 11 operations where 2 are below confidence threshold
  Then 9 operations are auto-applied to the model
  And 2 operations are queued for review in the ChangeSet
  And the output contains "below threshold"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/propose.py` | 75–164 | `DEFAULT_CONFIDENCE_THRESHOLD = 0.80` |
| `src/yggdrasil/changeset/services.py` | 62–140 | Auto-apply vs pending item status |
| `ratatosk/cli.py` | stdout | Surface pending/below threshold counts |
| `docs/plans/bootstrap-mvp/00-foundation/SHARED-CONTRACT.md` | ChangeSet review | Locked 0.80 threshold |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT auto-apply below 0.80 without human approve (except scripted test fixtures with explicit low-confidence ops).
- Do NOT use `set_model_mode` to bypass review in bootstrap certification.

---

## SAO.md Sections That Apply

- ChangeSet invariant + confidence gating

---

## Current State Assessment

Auto-apply logic exists in `ChangeSetService.propose` — CLI stdout may not print `below threshold` phrase yet. Scenario uses synthetic 11-op fixture, not sample_webapp alone.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_propose_auto_apply_nine_pending_two` | integration | 9 applied, 2 pending |
| `test_cli_stdout_below_threshold_phrase` | integration | stdout contains phrase when pending>0 |
| `test_cli05_behave_fixture_changeset` | behave | table-driven 11 ops |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ChangeSetService.propose` | per op | confidence, action=auto_apply|pending |
| `propose_changeset` | summary | applied_count, pending_count, threshold=0.80 |
| `ratatosk.cli` | handoff exit | below_threshold_count |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `propose_changeset` | Returns applied/pending counts |
| `approve_changeset` | Tier 2 path for pending ops |

---

## Implementation Steps

1. Factory fixture: 11 ops with 2 at confidence 0.65.
2. Assert service counts.
3. Print `below threshold: 2` in CLI when pending_count > 0.
4. Behave scenario with seeded ChangeSet (not full bootstrap).

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_propose_changeset.py::test_propose_auto_apply_nine_pending_two -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given a ChangeSet with 11 operations where 2 are below confidence threshold` | `changeset_steps.py` |
| `Then the output contains "below threshold"` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
