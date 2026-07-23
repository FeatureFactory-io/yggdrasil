# MCP-PROPOSE-CHANGESET — Server tool for Ratatosk bootstrap handoff

**Tier:** 1
**Wave:** W2
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature` (DISC-21)
**Package:** `05-mcp-handoff/`
**Depends on:** W0 foundation, ChangeSetService
**Blocks:** ACT-1-DISC-01, ACT-1-DISC-21, ACT-1-CLI-04 (enrichment hook)

---

## Scenario (Gherkin excerpt)

```gherkin
Scenario: ACT-1-DISC-21 Subprocess bootstrap calls MCP handoff tools
  ...
  Then MCP tool "propose_changeset" was called during bootstrap
```

---

## Why this scenario matters

Production Ratatosk **never** writes the graph via ORM. `propose_changeset` is the sole write path for bootstrap element ops (plus Munin-enriched relationships after CLI-04). W2 must prove schema, auth, auto-apply at 0.80, and `source=ratatosk` before discovery scenarios depend on it.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/propose.py` | 74–154 | Tool implementation |
| `src/yggdrasil/changeset/services.py` | 62–140 | `ChangeSetService.propose` |
| `src/yggdrasil/ratatosk/handoff.py` | 155–210 | `McpHandoffPort.propose` client wrapper |
| `src/yggdrasil/mcp/tests/test_propose_changeset.py` | all | Existing tests — extend |
| `tests/integration/mcp_harness/` | all | HTTP tool invocation pattern |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT accept `user_id` in tool args — derive from Bearer PAT server-side.
- Do NOT skip ChangeSetItem creation for auto-applied ops — audit trail required.
- Do NOT invoke Munin relationship planning in W2 unless CLI-04 merged — document hook point only.

---

## SAO.md Sections That Apply

- §18.4 `propose_changeset` contract
- §18.5 Auth — read-only token → PermissionError before write
- ChangeSet invariant — `source=ratatosk`

---

## Current State Assessment

| Piece | State |
|-------|--------|
| `propose_changeset` MCP tool | Implemented — element ops only |
| Auto-apply ≥0.80 | Implemented in service |
| Read-only token rejection | Verify before propose |
| Munin enrichment | **Gap** — CLI-04 adds planner hook |
| MCP harness integration tests | Partial |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_propose_changeset_creates_ratatosk_source` | unit/integration | source field ratatosk |
| `test_propose_changeset_auto_applies_high_confidence` | integration | ops ≥0.80 applied |
| `test_propose_changeset_readonly_token_403` | integration | no ChangeSet row |
| `test_propose_changeset_mcp_harness_http` | harness | JSON schema stable |
| `test_propose_empty_operations_allow_empty` | integration | allow_empty flag honored |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `propose_changeset` | entry | model_id, op_count, source, user_id (from auth) |
| `propose_changeset` | auth fail | reason=readonly_token |
| `ChangeSetService.propose` | auto-apply | applied_ids, pending_ids, threshold |
| `propose_changeset` | exit | changeset_id, status, applied_count, pending_count |

---

## MCP Tools to Expose

| Tool | Service method | Write? | Auth |
|------|---------------|--------|------|
| `propose_changeset` | `ChangeSetService.propose` | Yes | Bearer PAT, server user |

---

## Implementation Steps

1. **Red:** Harness test POST propose with sample element ops.
2. **Green:** Verify response `{changeset_id, applied_count, pending_count, status}`.
3. **Green:** Read-only PAT test — 403, no DB row.
4. **Green:** Wire `McpHandoffPort` to same endpoint CLI uses.
5. **Document:** Hook comment in propose.py for `MuninBootstrapPlanner` (CLI-04).
6. **Refactor:** Keep tool handler ≤30 lines — delegate to service.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_propose_changeset.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Then MCP tool "propose_changeset" was called during bootstrap` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-validate-api-contracts.mdc
- do-informative-logging.mdc
