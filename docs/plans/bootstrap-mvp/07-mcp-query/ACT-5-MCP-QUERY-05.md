# ACT-5-MCP-QUERY-05 — list_elements with stereotype filter

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** ACT-5-MCP-QUERY-01

---

## Scenario (Gherkin)

```gherkin
When Priya calls MCP tool "list_elements" with stereotype Container
Then response contains Payment API and Notification Service
And does not contain Mobile App or PostgreSQL
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | list_elements | Add stereotype filter param |
| `src/yggdrasil/graph/services.py` | list | Filter at ORM queryset |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- §18.4 list_elements params

---

## Current State Assessment

Stereotype filter may be unimplemented on MCP tool — REST may have precedent.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_elements_filter_container` | integration | inclusion/exclusion table |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_elements` | filter applied | stereotype=Container |

---

## MCP Tools to Expose

| Tool | Change |
|------|--------|
| `list_elements` | Optional `stereotype` param |

---

## Implementation Steps

1. Add stereotype param to tool schema.
2. Pass to service filter.
3. Red/green with seed elements.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_elements_filter_container -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
