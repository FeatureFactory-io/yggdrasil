# ACT-5-MCP-CHANGESET-01 — approve_changeset applies all pending operations

**Tier:** 2
**Wave:** W8
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`
**Depends on:** MCP-PROPOSE-CHANGESET, seed pending ChangeSet
**Blocks:** — (Tier 2 query/review path)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-5-MCP-CHANGESET-01 approve_changeset applies all pending operations
  Given ChangeSet id=1 has 6 pending operations
  When the CI agent calls approve_changeset id=1
  Then all 6 operations applied
  And ChangeSet status "applied"
```

---

## Why this scenario matters

Bootstrap auto-applies ≥0.80, but **sub-threshold ops stay pending** (CLI-05). This scenario proves headless review — Marcus approves via MCP without browser — completing the ChangeSet lifecycle for MVP Tier 2.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/changeset.py` | approve_changeset | Tool handler |
| `src/yggdrasil/changeset/services.py` | approve | Apply pending items |
| `src/yggdrasil/mcp/tests/test_approve_changeset.py` | all | Extend |
| SHARED-CONTRACT | 0.80 | Auto-apply does not replace manual approve for low confidence |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT use `set_model_mode` to bypass review in certification tests.
- Do NOT approve with read-only token.

---

## SAO.md Sections That Apply

- §18.4 approve_changeset
- ChangeSet invariant

---

## Current State Assessment

approve_changeset may exist from Act 0 — verify applies all pending atomically.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_approve_changeset_applies_all_six` | integration | 6 ops applied, status applied |
| `test_approve_changeset_readonly_rejected` | integration | 403 |
| `test_changeset01_behave` | behave | mcp_steps |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `approve_changeset` | entry | changeset_id, user_id, item_count |
| `ChangeSetService.approve` | each op | item_id, op_type, element_id |
| `approve_changeset` | exit | status=applied, applied_count=6 |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `approve_changeset` | ChangeSetService.approve | Yes |

---

## Implementation Steps

1. Factory ChangeSet 6 pending ops.
2. Red approve via MCP client.
3. Green graph reflects all 6 mutations.
4. TFK-07 CI agent step variant.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When the CI agent calls MCP tool "approve_changeset" with:` | `mcp_steps.py` |
| `Then all {n:d} operations are applied to the model` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
