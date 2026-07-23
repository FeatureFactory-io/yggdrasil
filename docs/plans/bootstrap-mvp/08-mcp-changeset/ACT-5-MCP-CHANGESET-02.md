# ACT-5-MCP-CHANGESET-02 — approve_changeset with item_ids partial approve

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`
**Depends on:** ACT-5-MCP-CHANGESET-01

---

## Scenario (Gherkin)

```gherkin
When Priya calls approve_changeset id=1 item_ids [1, 2]
Then operations 1 and 2 applied; 3-6 remain pending
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/changeset/services.py` | approve partial | item_ids filter |
| `src/yggdrasil/mcp/tools/changeset.py` | approve | Pass item_ids param |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- §18.4 approve_changeset partial

---

## Current State Assessment

Partial approve may be unimplemented — verify service API.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_approve_changeset_partial_item_ids` | integration | 2 applied, 4 pending |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `approve_changeset` | partial | item_ids, applied_count, remaining_pending |

---

## MCP Tools to Expose

| Tool | Change |
|------|--------|
| `approve_changeset` | Optional `item_ids` array |

---

## Implementation Steps

1. Extend service approve(filter=item_ids).
2. Red partial test.
3. Behave scenario.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py::test_approve_changeset_partial_item_ids -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
