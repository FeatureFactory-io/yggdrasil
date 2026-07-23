# MUNIN-BRIEFING-1-07 — C4 primer overlay on first bootstrap

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
"C4 in 60 seconds" and c4-primer-got-it visible.

## Context Map
| File | Note |
|------|------|
| User profile / session | first_bootstrap flag |
| HTMX overlay partial | primer component |

## Tests to Create
`test_briefing07_c4_primer_first_run` — integration with first-run user

## Logs to Emit
BriefingView: show_c4_primer=true, user_first_bootstrap=true

## Implementation Steps
Track first bootstrap on user/session; show dismissible overlay.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing07_c4_primer_first_run -x`

## Rules Applied
do-test-first.mdc, do-semantic-versioning-on-ui-elements.mdc
