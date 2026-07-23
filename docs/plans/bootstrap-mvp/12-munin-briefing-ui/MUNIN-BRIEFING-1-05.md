# MUNIN-BRIEFING-1-05 — Suggested next steps visible

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
Elements next-review-changeset, next-explore-graph, next-run-again visible.

## Context Map
| File | Note |
|------|------|
| munin-briefing.feature | testid list |
| docs/conventions.md | Screen ID traceability |

## Tests to Create
`test_briefing05_next_step_testids` — integration

## Logs to Emit
BriefingView: next_steps_rendered=3

## Implementation Steps
Add three CTA blocks with data-testid per feature file.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing05_next_step_testids -x`

## Rules Applied
do-semantic-versioning-on-ui-elements.mdc, do-test-first.mdc
