# ACT-5-MCP-QUERY-08 — get_changeset returns operations and Munin reasoning

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** MCP-PROPOSE-CHANGESET, ACT-1-CLI-04

---

## Scenario (Gherkin)

```gherkin
Given ChangeSet id=1 (run-003, pending, 6 operations)
When Priya calls get_changeset id=1
Then 6 operations, Notification Service in Add Element op, munin_reasoning field
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | get_changeset | |
| `src/yggdrasil/changeset/models.py` | ChangeSetItem | Operations list |
| `src/yggdrasil/mcp/tools/propose.py` | munin_reasoning | Stored on propose |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- §18.4 get_changeset

---

## Current State Assessment

Fixture ChangeSet id=1 with 6 ops — align with journey seed or factory.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_get_changeset_six_ops` | integration | count + munin_reasoning key |
| `test_get_changeset_includes_notification_service` | integration | op detail substring |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `get_changeset` | entry | changeset_id, user_id |
| `get_changeset` | exit | operation_count, status |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `get_changeset` | ChangeSetQueryService.get | No |

---

## Implementation Steps

1. Seed ChangeSet id=1 fixture per feature narrative.
2. Red get_changeset test.
3. Serializer includes munin_reasoning + op list.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_get_changeset_six_ops -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the model has ChangeSet id={id}` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-validate-api-contracts.mdc
- do-informative-logging.mdc
