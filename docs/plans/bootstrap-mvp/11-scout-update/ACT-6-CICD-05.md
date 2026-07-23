# ACT-6-CICD-05 — CI pipeline links to run result URL

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
Update completes → stdout URL to RATATOSK_RUN-VIEW for new run.

## Context Map
| File | Note |
|------|------|
| `ratatosk/cli.py` | print run URL (mirror CLI-01) |
| MCP-RECORD-RATOSK-RUN | run_id in response |

## Tests to Create
`test_cicd05_run_url_in_output` — integration

## Logs to Emit
exit: run_url printed

## MCP Tools to Expose
record_ratatosk_run returns url

## Implementation Steps
Reuse CLI-01 URL formatting with trigger=update.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd05_run_url_in_output -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
