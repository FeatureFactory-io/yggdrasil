# ACT-6-CICD-12 — MCP snapshot failure mid-update creates no ChangeSet

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
MCP unreachable during update → exit ≠ 0, `MCP`, no ratatosk ChangeSet for run.

## Context Map
| File | Note |
|------|------|
| DISC-13 | same failure semantics |
| mcp_harness | 503 injection |

## Tests to Create
`test_cicd12_mcp_fail_no_changeset` — integration harness

## Logs to Emit
abort: reason=mcp_snapshot_failed, command=update

## Checkpoint
`pytest tests/integration/mcp_harness/test_cicd12_mcp_fail_no_changeset.py -x`

## Rules Applied
do-test-first.mdc, do-not-mock-in-integration-tests.mdc
