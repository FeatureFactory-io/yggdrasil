# MUNIN-BRIEFING-1-06 — Direct action buttons to ChangeSet and graph

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
review-changeset-btn and explore-graph-btn visible.

## Context Map
| File | Note |
|------|------|
| act-7 changeset-view | review URL |
| act-2 view-browse | graph browser |

## Tests to Create
`test_briefing06_action_buttons_visible` — integration

## Implementation Steps
Wire hrefs to real routes with run's changeset_id and model slug.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing06_action_buttons_visible -x`

## Rules Applied
do-semantic-versioning-on-ui-elements.mdc
