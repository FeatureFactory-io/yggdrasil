# MUNIN-BRIEFING-1-02 — Briefing shows Munin auto-generated narrative

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
Page shows "I analysed", "elements", "relationships", "Munin planned relationships".

## Context Map
| File | Note |
|------|------|
| ChangeSet munin_reasoning | source text |
| CLI-04 planner summary | bootstrap narrative |

## Tests to Create
`test_briefing02_narrative_from_munin_reasoning` — integration

## Logs to Emit
BriefingView: munin_reasoning_len, rendered=true

## Implementation Steps
Render munin_reasoning from linked ChangeSet; format for HTML.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing02_narrative_from_munin_reasoning -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
