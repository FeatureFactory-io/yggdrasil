# ACT-6-CICD-13 — Update never writes Elements outside ChangeSet

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
update with pr.diff → ChangeSet ratatosk, no orphan Elements.

## Context Map
| File | Note |
|------|------|
| DISC-06 | same invariant on update path |

## Tests to Create
`test_cicd13_no_orphans_on_update` — integration

## Logs to Emit
invariant check orphan_count=0 post-update

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd13_no_orphans_on_update -x`

## Rules Applied
do-test-first.mdc, do-not-mock-in-integration-tests.mdc
