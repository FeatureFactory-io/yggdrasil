# ACT-1-SCOUT-03 — Scout probes Yggdrasil MCP for existing elements

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-scout.feature`

## Scenario (Gherkin)
```gherkin
Given model has element Payment API
When Marcus pipes pr.diff into update
Then MCP search or get_element recorded on blackboard
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/mcp_client.py` | scout calls | search/get_element |
| `src/yggdrasil/mcp/tools/query.py` | search | Server tools from W7 |

## Do Not Do
Inherit SHARED-CONTRACT — MCP read only during scout.

## SAO.md Sections That Apply
- A5.6 Yggdrasil MCP tools for scout

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_scout03_mcp_search_recorded` | integration | tool_calls mcp.yggdrasil |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| scout MCP call | each | tool_name, query or id |

## MCP Tools to Expose
`search`, `get_element` — consumed by scout client.

## Implementation Steps
1. Wire scout to call MCP when diff mentions known slugs.
2. Record on blackboard tool_calls with connector mcp.yggdrasil.
3. Depends on W7 query tools green.

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_scout03_mcp_search_recorded -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
