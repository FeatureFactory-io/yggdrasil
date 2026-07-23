# ACT-6-CICD-08 — README prose on stdin produces delta

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-update.feature`

## Scenario (Gherkin)
architecture-notes.md stdin → input_mode stdin, kind prose, ChangeSet exists.

## Context Map
| File | Note |
|------|------|
| `tests/fixtures/repos/sample_stdin/architecture-notes.md` | prose fixture |
| runner stdin classifier | diff vs prose |

## Tests to Create
`test_cicd08_prose_stdin_mode` — blackboard keys

## Logs to Emit
stdin classify: kind=prose

## Implementation Steps
1. Detect non-diff stdin as prose.
2. Set blackboard input_mode/kind.
3. Still produce ChangeSet when LLM finds ops.

## Checkpoint
`pytest ratatosk/tests/test_update_cli.py::test_cicd08_prose_stdin_mode -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
