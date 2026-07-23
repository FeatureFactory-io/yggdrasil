# MUNIN-BRIEFING-1-10 — Navbar with View Browser link

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
nav-view-browser and nav-elements visible on briefing page.

## Context Map
| File | Note |
|------|------|
| Base template navbar | shared layout |
| act-2 view-browse | nav-view-browser target |

## Tests to Create
`test_briefing10_navbar_links` — integration

## Implementation Steps
Include standard navbar partial on briefing template; testids per IA guidelines.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing10_navbar_links -x`

## Rules Applied
do-semantic-versioning-on-ui-elements.mdc, docs/ux/IA_guidelines.md
