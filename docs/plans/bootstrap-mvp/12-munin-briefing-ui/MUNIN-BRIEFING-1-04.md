# MUNIN-BRIEFING-1-04 — Key findings with links

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
User sees "Payment API" with links to elements or ChangeSets.

## Context Map
| File | Note |
|------|------|
| Element detail URLs | graph web act-3 |
| ChangeSet review URLs | act-7 |

## Tests to Create
`test_briefing04_payment_api_link_present` — integration

## Logs to Emit
BriefingView: findings_count, linked_element_slugs

## Implementation Steps
Parse key element names from munin_reasoning or blackboard; render anchor tags.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing04_payment_api_link_present -x`

## Rules Applied
do-test-first.mdc, do-semantic-versioning-on-ui-elements.mdc
