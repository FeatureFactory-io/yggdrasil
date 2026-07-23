# ACT-6-CICD-01 — ratatosk update on PR diff produces incremental ChangeSet

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature` | **Package:** `11-scout-update/`

## Scenario (Gherkin)
PR diff via stdin → exit 0, `building ModelSummary`, ChangeSet source ratatosk.

## Context Map
| File | Note |
|------|------|
| `ratatosk/cli.py` update command | stdin pipe entry |
| `ratatosk/discovery/runner.py` | update orchestration |
| `tests/fixtures/repos/sample_stdin/pr.diff` | stdin fixture |

## Do Not Do
Inherit SHARED-CONTRACT — update never wipes.

## SAO.md Sections That Apply
§17.3 update incremental path

## Tests to Create
`test_cicd01_update_produces_changeset` — integration

## Logs to Emit
update entry: trigger=stdin_diff; ModelSummary step; handoff changeset_id

## MCP Tools to Expose
propose_changeset, record_ratatosk_run

## Implementation Steps
1. Wire update command to runner update mode.
2. ModelSummary before scout (CICD-03).
3. Handoff delta buckets.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd01_update_produces_changeset -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
