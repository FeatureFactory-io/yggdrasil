# ACT-5-MCP-QUERY-06 — list_elements with as_of historical snapshot

> **DEFER (Tier 4)** — Implement after W0–W9 green. Requires time-travel / history infrastructure.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** Act 2 view-history (out of bootstrap MVP scope)

---

## Scenario (Gherkin)

```gherkin
When Elena calls list_elements with as_of 2026-01-01
Then response reflects model state as of that date
And metadata indicates historical timestamp
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `docs/features/act-2-view/view-history.feature` | all | Historical query semantics |
| `src/yggdrasil/graph/` | history | May not exist in MVP |

---

## Do Not Do

Inherit SHARED-CONTRACT — do not fake as_of without audit trail backing.

---

## SAO.md Sections That Apply

- Time-travel (if documented in SAO Part II)

---

## Current State Assessment

**Likely not implemented** — defer until history tables/events exist.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_elements_as_of_date` | integration | snapshot at date |
| `test_list_elements_as_of_metadata` | integration | header timestamp |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_elements` | as_of | requested_date, resolved_snapshot_id |

---

## MCP Tools to Expose

| Tool | Change |
|------|--------|
| `list_elements` | Optional `as_of` ISO date |

---

## Implementation Steps

1. Design history snapshot API with Act 2 team.
2. Implement service method.
3. Wire MCP param + metadata header.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_elements_as_of_date -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
