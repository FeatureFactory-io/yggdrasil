# ACT-1-SCOUT-04 — Scout optionally fetches linked issue via Atlassian MCP

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-scout.feature` @wip

## Scenario (Gherkin)
```gherkin
When Marcus pipes commit "feat(llm.planner): ... #MIM-056" into update
Then tool_calls connector "mcp.atlassian" and source issue MIM-056
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/config.py` | connectors | allow mcp.atlassian |
| `ratatosk/discovery/scout.py` | issue parse | #KEY regex |

## Do Not Do
Inherit SHARED-CONTRACT — secrets via env:VAR only (CFG-04).

## SAO.md Sections That Apply
- A4.5 external MCP Atlassian

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_scout04_atlassian_connector_when_allowed` | integration | @wip mock connector |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| atlassian fetch | call | issue_key, connector=mcp.atlassian |

## MCP Tools to Expose
External Atlassian MCP — not Yggdrasil server; mock in tests.

## Implementation Steps
1. Parse issue keys from stdin.
2. If config allows, call connector MCP get_issue.
3. Record provenance on blackboard.

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_scout04_atlassian_connector_when_allowed -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
