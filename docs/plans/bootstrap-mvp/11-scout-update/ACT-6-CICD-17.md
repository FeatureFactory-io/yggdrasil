# ACT-6-CICD-17 — Commit log triggers scout with repo reads

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature` @wip

## Scenario (Gherkin)
Commit message stdin feat(llm.planner)... → scout_plan includes path src/llm/planner.

## Context Map
| File | Note |
|------|------|
| SCOUT-01 | scout_plan step |
| commit parser | extract path hints from message |

## Tests to Create
`test_cicd17_commit_triggers_scout_paths` — integration

## Logs to Emit
scout_plan: paths_from_commit_message

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_cicd17_commit_triggers_scout_paths -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
