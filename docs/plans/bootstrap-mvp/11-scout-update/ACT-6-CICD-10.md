# ACT-6-CICD-10 — Stdin over size cap fails without inventing Elements

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
Stdin > cap → exit ≠ 0, output `limit`, no orphan Elements.

## Context Map
| File | Note |
|------|------|
| `ratatosk/discovery/runner.py` | STDIN_SIZE_CAP_BYTES |
| DISC-06 | orphan invariant |

## Tests to Create
`test_cicd10_stdin_over_cap` — integration

## Logs to Emit
reject: stdin_bytes, cap, reason=over_limit

## Implementation Steps
1. Check stdin size before processing.
2. Exit non-zero with limit message.
3. Assert no graph mutations.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd10_stdin_over_cap -x`

## Rules Applied
do-test-first.mdc, do-not-mock-in-integration-tests.mdc
