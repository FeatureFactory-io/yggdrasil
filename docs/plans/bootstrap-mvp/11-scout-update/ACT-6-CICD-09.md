# ACT-6-CICD-09 — Empty stdin yields no architecture changes

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
Empty stdin → exit 0, `no architecture changes detected`.

## Context Map
| File | Note |
|------|------|
| `ratatosk/cli.py` | stdin read |
| STDIN_SIZE_CAP_BYTES | zero length handling |

## Tests to Create
`test_cicd09_empty_stdin` — integration

## Logs to Emit
stdin: length=0, action=early_exit_empty

## Implementation Steps
Fail fast on empty stdin with friendly message — no scout.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd09_empty_stdin -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
