# ACT-1-CFG-03 — Tool allowlist restricts scout connectors

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-config.feature`

## Scenario (Gherkin)
```gherkin
Given tools allow local, mcp.yggdrasil; disallows mcp.atlassian
When update with commit referencing #MIM-056
Then no mcp.atlassian tool call recorded
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/config.py` | tools.allow | Allowlist |
| `ratatosk/discovery/scout.py` | connector gate | Before external MCP |

## Do Not Do
Inherit SHARED-CONTRACT.

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_cfg03_disallowed_connector_blocked` | integration | no atlassian in tool_calls |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| scout | connector blocked | connector=mcp.atlassian, reason=not_allowed |

## MCP Tools to Expose
N/A — config gates client-side connector calls.

## Implementation Steps
1. Parse tools.allow from config.
2. Skip disallowed connector calls with INFO log.
3. Test with SCOUT-04 stdin without atlassian call.

## Checkpoint
`pytest ratatosk/tests/test_config_loader.py::test_cfg03_disallowed_connector_blocked -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
