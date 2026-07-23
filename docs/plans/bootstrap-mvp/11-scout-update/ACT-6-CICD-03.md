# ACT-6-CICD-03 — ModelSummary before scout gather on update

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
Populated model 31/44 + pr.diff → `building ModelSummary` before ops; ChangeSet only diff-affected elements.

## Context Map
| File | Note |
|------|------|
| `ratatosk/discovery/runner.py` | step order ModelSummary → scout |
| ACT-1-DISC-15 | Shared ModelSummary builder |

## Do Not Do
Inherit SHARED-CONTRACT — no full graph in prompt.

## Tests to Create
`test_cicd03_model_summary_before_scout` — log order + op scope

## Logs to Emit
step order: model_summary then scout_plan

## MCP Tools to Expose
list_elements for reconcile snapshot in code (not prompt)

## Implementation Steps
1. Reuse DISC-15 ModelSummary on update path.
2. Assert stdout order.
3. Limit ChangeSet ops to diff slugs.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd03_model_summary_before_scout -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
