# ACT-5-MCP-QUERY-02 — search returns matching elements by name

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** ACT-5-MCP-QUERY-01 seed

---

## Scenario (Gherkin)

```gherkin
When Priya calls MCP tool "search" with query Payment, model Yggdrasil
Then the response contains "Payment API"
And the response does not contain "Order Domain"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | search | ILIKE / trigram on name |
| `src/yggdrasil/graph/services.py` | search | Shared search service |

---

## Do Not Do

Inherit SHARED-CONTRACT — read-only; scope results to authorized model.

---

## SAO.md Sections That Apply

- §18.4 `search`

---

## Current State Assessment

Verify search tool registered; may delegate to same service as REST search endpoint.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_search_payment_matches_api_only` | integration | Payment API in, Order Domain out |
| `test_search_empty_query_rejects` | unit | Validation error |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `search` | entry | query_len, model, user_id |
| `search` | exit | hit_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `search` | ElementQueryService.search | No |

---

## Implementation Steps

1. Red MCP harness search call.
2. Green wire service + model filter.
3. Behave step with param table.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_search_payment_matches_api_only -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "search" with:` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
