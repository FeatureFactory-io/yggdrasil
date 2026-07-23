# ACT-6-CICD-04 — Incremental update produces delta buckets without wiping

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
No `wiping` in output; delta buckets to_add/to_update/to_delete mins; unchanged not sent to Munin.

## Context Map
| File | Note |
|------|------|
| `ratatosk/discovery/runner.py` | update reconcile mode |
| RATATOSK-SPEC A3 | update ≠ bootstrap |

## Do Not Do
Inherit SHARED-CONTRACT — never call wipe on update.

## Tests to Create
`test_cicd04_no_wipe_delta_buckets` — integration

## Logs to Emit
reconcile mode=incremental_update

## MCP Tools to Expose
Not applicable.

## Implementation Steps
1. Separate reconcile from bootstrap_post_wipe.
2. Print delta bucket table.
3. Negative assert on wiping.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd04_no_wipe_delta_buckets -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
