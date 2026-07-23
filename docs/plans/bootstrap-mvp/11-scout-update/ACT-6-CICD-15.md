# ACT-6-CICD-15 — Diff removing mapped service auto-proposes to_delete

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature` @wip

## Scenario (Gherkin)
Model has Legacy Service; diff removes it from codebase → to_delete bucket ≥1, ChangeSet exists.

## Context Map
| File | Note |
|------|------|
| RATATOSK-SPEC A9 | to_delete auto-propose policy |
| reconcile | map codebase removal to delete op |

## Do Not Do
Bootstrap bulk wipe — per-element to_delete is update-only.

## Tests to Create
`test_cicd15_to_delete_on_service_removal` — @wip integration

## Logs to Emit
reconcile: to_delete_count, element=Legacy Service

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd15_to_delete_on_service_removal -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
