# MUNIN-BRIEFING-1-09 — Raw run log links to run view

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
User sees "run" text linking to RATATOSK_RUN-VIEW screen.

## Context Map
| File | Note |
|------|------|
| act-9 ratatosk_run-view | target screen |
| RataskRun blackboard | collapsible log section |

## Tests to Create
`test_briefing09_run_log_link` — integration

## Logs to Emit
BriefingView: run_detail_url generated

## Implementation Steps
Collapsible blackboard JSON + link to run detail view.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing09_run_log_link -x`

## Rules Applied
do-test-first.mdc, docs/conventions.md screen IDs
