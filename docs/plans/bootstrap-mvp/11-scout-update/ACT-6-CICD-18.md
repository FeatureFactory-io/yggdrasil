# ACT-6-CICD-18 — ModelSummary overflow triggers MCP drill-down during scout

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature` @wip

## Scenario (Gherkin)
200 elements + pr.diff → model_summary_chars on blackboard + list_elements MCP call recorded.

## Context Map
| File | Note |
|------|------|
| DISC-15 | ModelSummary budget |
| QUERY-01/W7 | list_elements for drill-down |

## Tests to Create
`test_cicd18_drill_down_list_elements` — integration large graph fixture

## Logs to Emit
ModelSummary: budget_exhausted=true, drill_down=list_elements

## MCP Tools to Expose
list_elements during scout when summary insufficient

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_cicd18_drill_down_list_elements -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
