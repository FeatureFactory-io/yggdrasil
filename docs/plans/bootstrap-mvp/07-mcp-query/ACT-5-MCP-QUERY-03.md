# ACT-5-MCP-QUERY-03 — get_element returns properties and relationships

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** ACT-1-CLI-04 (relationships), bootstrap seed with Payment API properties

---

## Scenario (Gherkin)

```gherkin
When Priya calls MCP tool "get_element" with id_or_name Payment API
Then the response contains name, stereotype Container, package Technology, owner payments-team
And properties.framework = FastAPI
And response contains confidence field
```

---

## Why this scenario matters

`get_element` is the **drill-down tool** Ratatosk scout uses when ModelSummary budget exhausted (SAO A5.6). Must return rich payload — not just name/stereotype — for Cursor agents answering "tell me about Payment API".

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | get_element | By id or slug/name |
| `src/yggdrasil/graph/models.py` | Element | properties JSON, confidence |
| `tests/fixtures/seed.json` | Payment API | owner, framework property |

---

## Do Not Do

Inherit SHARED-CONTRACT — no write side effects on read tool.

---

## SAO.md Sections That Apply

- §18.4 get_element
- A5.6 drill-down via get_element

---

## Current State Assessment

Seed must include `framework: FastAPI` on Payment API — verify seed.json vs sample_webapp manifest gap.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_get_element_by_name_full_payload` | integration | all Gherkin fields |
| `test_get_element_includes_confidence` | integration | confidence key present |
| `test_get_element_not_found` | integration | clear 404 |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `get_element` | entry | id_or_name, resolved_id |
| `get_element` | exit | stereotype, relationship_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `get_element` | ElementQueryService.get | No |

---

## Implementation Steps

1. Extend seed Payment API with properties + confidence.
2. Red test for field table assertions.
3. Green serializer includes properties dict + relationships summary.
4. Behave mcp_steps field table matcher.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_get_element_by_name_full_payload -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Then the response contains:` (field table) | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-validate-api-contracts.mdc
- do-informative-logging.mdc
