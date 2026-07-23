# ACT-6-CICD-06 — Update run visible in RATATOSK_RUN list UI

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
Browse /mockups/ratatosk-run/ → recent run trigger "ratatosk update".

## Context Map
| File | Note |
|------|------|
| `src/yggdrasil/web/` | run list view |
| `docs/features/act-9-ratatosk_run/` | list feature |

## Do Not Do
Quarantined mockup path — migrate to real route in same wave.

## Tests to Create
`test_cicd06_run_list_shows_update` — Django client integration

## Logs to Emit
view list: filter trigger=update

## MCP Tools to Expose
list_ratatosk_runs (QUERY-10 deferred)

## Implementation Steps
1. Record run with trigger=update.
2. Wire list view to real URL.
3. Assert most recent row.

## Checkpoint
`pytest tests/integration/test_ratatosk_run_list.py::test_cicd06_run_list_shows_update -x`

## Rules Applied
do-test-first.mdc, do-semantic-versioning-on-ui-elements.mdc
