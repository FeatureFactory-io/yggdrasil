# ACT-1-SCOUT-01 — Scout plan records evidence intents on blackboard

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-scout.feature` | **Package:** `11-scout-update/`

## Scenario (Gherkin)
```gherkin
When Marcus pipes stdin fixture "pr.diff" into ratatosk update with repo "./repo"
Then blackboard step "scout_plan" and key "evidence_plan"
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | update path | Scout plan step |
| `ratatosk/cli.py` | update | stdin + --repo |
| `tests/fixtures/repos/sample_stdin/pr.diff` | all | Trigger fixture |

## Do Not Do
Inherit SHARED-CONTRACT — update never wipes (CICD-19).

## SAO.md Sections That Apply
- A4 scout loop — plan evidence before gather

## Current State Assessment
Scout plan step likely missing on update path; bootstrap uses filesystem not scout.

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_scout01_blackboard_scout_plan` | integration | step + evidence_plan key |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| scout_plan | built | evidence_intent_count, stdin_kind=diff |

## MCP Tools to Expose
Not applicable at plan step.

## Implementation Steps
1. After stdin parse, LLM/heuristic builds evidence_plan list.
2. Record on blackboard before file reads.
3. Red/blackboard test with pr.diff.

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_scout01_blackboard_scout_plan -x`

## TFK-07 Steps Required
`pipes stdin fixture into ratatosk update` — `scout_steps.py`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
