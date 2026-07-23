# MUNIN-BRIEFING-1-01 — Briefing page renders after Ratatosk run

> **DEFER (Tier 4)** — Implement after W0–W9 green. Feature @wip quarantined (mockup URL).

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature` | **Screen:** MUNIN-BRIEFING-1

## Scenario (Gherkin)
GET briefing → 200, `munin-briefing-page` visible.

## Context Map
| File | Note |
|------|------|
| `src/yggdrasil/web/templates/` | briefing template |
| `docs/ux/IA_guidelines.md` | Screen patterns |
| `data-testid` munin-briefing-page | semantic versioning rule |

## Do Not Do
Ship mockup-only route as certification — wire real run_id param.

## SAO.md Sections That Apply
Web HTMX patterns — server-rendered partials

## Tests to Create
`test_briefing01_page_renders_200` — Django client + testid

## Logs to Emit
BriefingView GET: run_id, user_id, status=200

## MCP Tools to Expose
Not applicable.

## Implementation Steps
1. Create view bound to RataskRun pk/slug.
2. Template with data-testid munin-briefing-page.
3. Replace /mockups/ path in feature when live.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing01_page_renders_200 -x`

## TFK-07 Steps Required
`When I GET` / `element should be visible` — web_steps.py

## Rules Applied
do-test-first.mdc, do-semantic-versioning-on-ui-elements.mdc
