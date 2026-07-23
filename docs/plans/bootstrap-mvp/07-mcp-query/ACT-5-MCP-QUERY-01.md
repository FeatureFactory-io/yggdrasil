# ACT-5-MCP-QUERY-01 — list_elements returns paginated element list

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** W6 bootstrapped graph (CLI-04 relationships optional for count)
**Blocks:** QUERY-02, QUERY-05

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-5-MCP-QUERY-01 list_elements returns paginated element list
  Given ... model "Yggdrasil" contains 6 elements
  When Priya calls MCP tool "list_elements" with model Yggdrasil
  Then the response contains 6 elements
  And element "Payment API" ... stereotype "Container"
  And element "Mobile App" ... stereotype "System"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | list_elements | Tool handler |
| `src/yggdrasil/graph/services.py` | list | Service layer — shared with REST |
| `tests/fixtures/seed.json` | journey | 6-element post-bootstrap seed |
| `src/yggdrasil/mcp/server.py` | register | FastMCP registration |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT embed MCP-specific filtering in service — keep in tool args layer.
- Do NOT accept user_id in tool args.

---

## SAO.md Sections That Apply

- §18.4 read tools
- §Services layer shared by MCP and Web

---

## Current State Assessment

`list_elements` likely exists; pagination and journey seed with 6 elements including Mobile App — verify fixture alignment with bootstrap MVP (sample_webapp has 4 — seed may extend).

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_elements_returns_count` | integration MCP | len == 6 |
| `test_list_elements_payment_api_container` | integration | name + stereotype |
| `test_list_elements_pagination_default` | unit | page size stable |
| `test_query01_behave` | behave | TFK-07 mcp_steps |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_elements` | entry | model, user_id from auth, page |
| `list_elements` | exit | result_count, duration_ms |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `list_elements` | ElementQueryService.list | No |

---

## Implementation Steps

1. Seed 6-element graph fixture for MCP tests.
2. Red integration test via InProcessMcpToolClient.
3. Green align response schema with feature table fields.
4. TFK-07 mcp_steps for tool invocation.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_elements_returns_count -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "list_elements" with:` | `mcp_steps.py` |
| `Then the response contains {n:d} elements` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-validate-api-contracts.mdc
- do-informative-logging.mdc
