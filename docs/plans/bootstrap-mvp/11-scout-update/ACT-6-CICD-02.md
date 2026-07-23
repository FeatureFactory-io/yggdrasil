# ACT-6-CICD-02 — Update with instructions focuses on changed interfaces

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
`--instructions` on update → to_add or to_update; unchanged never sent to Munin.

## Context Map
| File | Note |
|------|------|
| `ratatosk/cli.py` | --instructions on update |
| `ratatosk/discovery/runner.py` | filter unchanged before handoff |

## Do Not Do
Inherit SHARED-CONTRACT.

## Tests to Create
`test_cicd02_instructions_in_prompt` — integration

## Logs to Emit
handoff: skipped_unchanged_count, instructions_len

## MCP Tools to Expose
propose_changeset (delta ops only)

## Implementation Steps
1. Pass instructions to scout/extract LLM context.
2. Reconcile marks unchanged; exclude from operations list.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd02_instructions_in_prompt -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
