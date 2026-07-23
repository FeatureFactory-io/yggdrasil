# ACT-1-SCOUT-02 — Scout reads local files from --repo

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-scout.feature`

## Scenario (Gherkin)
```gherkin
When Marcus pipes pr.diff into update with repo from fixture sample_webapp
Then blackboard tool_calls include source "local" and action "read_file"
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/scout.py` | read_file | Local tool impl |
| `tests/fixtures/repos/sample_webapp/` | all | --repo target |

## Do Not Do
Inherit SHARED-CONTRACT — require --repo for local reads.

## SAO.md Sections That Apply
- A4.3 local tools read_file, list_dir

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_scout02_local_read_file_recorded` | integration | tool_calls entry |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| read_file | each | path, bytes_read, source=local |

## MCP Tools to Expose
Not applicable — local tool not Yggdrasil MCP.

## Implementation Steps
1. Implement read_file with repo root join + bounds.
2. Append to blackboard tool_calls.
3. Test with sample_webapp path from pr.diff hints.

## Checkpoint
`pytest src/yggdrasil/ratatosk/tests/test_scout_loop.py::test_scout02_local_read_file_recorded -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
