# ACT-1-CFG-01 — Repo ratatosk.yaml overrides home scout bounds

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-config.feature`

## Scenario (Gherkin)
```gherkin
Given home config scout max_rounds 10 and repo config max_rounds 5
When update with repo and pr.diff stdin
Then effective scout max_rounds is 5
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/config.py` | merge | repo overrides home |
| `ratatosk/discovery/scout.py` | bounds | Enforce max_rounds |

## Do Not Do
Inherit SHARED-CONTRACT — merge order flags→env→repo→home.

## SAO.md Sections That Apply
- A7.3 config merge

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_cfg01_repo_overrides_home_scout_rounds` | unit | effective=5 |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| load_config | merge | scout.max_rounds, source=repo |

## MCP Tools to Expose
Not applicable.

## Implementation Steps
1. Extend config schema for scout.max_rounds.
2. Merge test with two YAML fixtures.
3. Scout loop stops at 5 rounds in integration test.

## Checkpoint
`pytest ratatosk/tests/test_config_loader.py::test_cfg01_repo_overrides_home_scout_rounds -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
