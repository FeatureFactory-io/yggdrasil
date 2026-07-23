# ACT-5-MCP-CHANGESET-06 — CI mixed confidence approve and redirect

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`
**Depends on:** CHANGESET-01, CHANGESET-05, CLI-05 semantics

---

## Scenario (Gherkin)

```gherkin
Given post-merge ChangeSet 5 ops with confidence table
When CI approves item_ids [1,2,3] (>=0.80) and do_other for op 5
Then 1-3 applied, 4 pending, 5 redirected
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `docs/features/act-5-mcp/mcp-changeset.feature` | CHANGESET-06 | Composite workflow |
| `src/yggdrasil/mcp/tools/changeset.py` | approve + do_other | Orchestration in CI script |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- Act 6 CI agent patterns

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_ci_mixed_confidence_workflow` | integration | end state per table |
| `test_ci_script_example` | docs | Reference script in tests/fixtures |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| CI workflow | summary | applied=3, pending=1, redirected=1 |

---

## MCP Tools to Expose

Composite — `approve_changeset` + `do_other_changeset`.

---

## Implementation Steps

1. Seed 5-op fixture with confidence column.
2. Script sequential MCP calls mirroring scenario.
3. Assert final graph + ChangeSet states.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py::test_ci_mixed_confidence_workflow -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
