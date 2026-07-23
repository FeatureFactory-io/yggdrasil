# ACT-5-MCP-QUERY-07 — list_changesets returns pending and applied

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** Bootstrap + pending sub-threshold ops (CLI-05 deferred) or manual seed

---

## Scenario (Gherkin)

```gherkin
When Priya calls MCP tool "list_changesets" with no params
Then response contains ChangeSet status pending and applied
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | list_changesets | |
| `src/yggdrasil/changeset/services.py` | list | Filter by user/model RBAC |

---

## Do Not Do

Inherit SHARED-CONTRACT — respect token scope and model access.

---

## SAO.md Sections That Apply

- §18.4 list_changesets

---

## Current State Assessment

Seed needs at least one pending and one applied ChangeSet for assertion.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_changesets_mixed_status` | integration | both statuses present |
| `test_list_changesets_rbac` | integration | user isolation |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_changesets` | exit | pending_count, applied_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `list_changesets` | ChangeSetQueryService.list | No |

---

## Implementation Steps

1. Factory: one applied bootstrap CS + one pending manual CS.
2. Red list test.
3. Green MCP tool + behave step.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_changesets_mixed_status -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "list_changesets" with no params` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
