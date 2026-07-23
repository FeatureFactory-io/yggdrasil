# ACT-6-CICD-19 — Update never wipes the graph

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature` @wip

## Scenario (Gherkin)
31 elements + pr.diff update → no `wiping`, element count still 31.

## Context Map
| File | Note |
|------|------|
| CLI-02/08 | wipe bootstrap only |
| RATATOSK-SPEC A3 | update incremental |

## Tests to Create
`test_cicd19_update_never_wipes` — integration regression guard

## Logs to Emit
update: wipe_called=false, element_count_before=after=31

## Do Not Do
Never invoke bulk_wipe_model from update command.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd19_update_never_wipes -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
