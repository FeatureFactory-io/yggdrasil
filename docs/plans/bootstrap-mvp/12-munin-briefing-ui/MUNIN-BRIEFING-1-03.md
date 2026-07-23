# MUNIN-BRIEFING-1-03 — Confidence distribution counts

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `munin-briefing.feature`

## Scenario (Gherkin)
Shows auto-applied, queued for review, below threshold.

## Context Map
| File | Note |
|------|------|
| ChangeSetItem status | applied vs pending |
| SHARED-CONTRACT 0.80 | threshold labels |

## Tests to Create
`test_briefing03_confidence_buckets_displayed` — seed mixed confidence CS

## Logs to Emit
BriefingView: auto_count, pending_count, below_threshold_count

## Implementation Steps
Aggregate ChangeSetItem by confidence vs threshold; render three counts.

## Checkpoint
`pytest tests/integration/test_munin_briefing_views.py::test_briefing03_confidence_buckets_displayed -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
