# ACT-1-SCOUT-05 — Element candidates carry provenance from scout sources

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-scout.feature`

## Scenario (Gherkin)
```gherkin
When Marcus pipes pr.diff into update
Then every element candidate has provenance source recorded
And ChangeSet source ratatosk exists
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | candidates | sources[] on each |
| `docs/plans/RATATOSK-SPEC-REALIGNMENT-PLAN.md` | A8 | Provenance spec |

## Do Not Do
Inherit SHARED-CONTRACT — handoff still via ChangeSet only.

## SAO.md Sections That Apply
- A8.1 candidate sources[]

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_scout05_candidate_provenance` | integration | all candidates have sources |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| extract | per candidate | name, sources_count |

## MCP Tools to Expose
Not applicable.

## Implementation Steps
1. Attach sources from tool_calls to candidates.
2. Pass through handoff to Munin/blackboard.
3. Assert non-empty sources[] on each candidate.

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_scout05_candidate_provenance -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
