# MUNIN-BRIEFING-1-08 — C4 primer explains four levels

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
Text Context, Container, Component, Code visible.

## Context Map
| File | Note |
|------|------|
| Primer template copy | static C4 education |
| C4 seed packages | alignment check |

## Tests to Create
`test_briefing08_primer_four_levels` — integration

## Implementation Steps
Static copy in primer partial — no LLM generation for primer.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing08_primer_four_levels -x`

## Rules Applied
do-test-first.mdc
