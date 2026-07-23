# ACT-6-CICD-11 — Missing token on update fails like bootstrap

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
update without token → exit ≠ 0, output `token`.

## Context Map
| File | Note |
|------|------|
| `ratatosk/cli.py` | `_require_token` on update |
| ACT-1-CLI-06 | shared behavior |

## Tests to Create
`test_cicd11_update_missing_token` — reuse CLI-06 helper

## Logs to Emit
reason=missing_token, command=update

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd11_update_missing_token -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
