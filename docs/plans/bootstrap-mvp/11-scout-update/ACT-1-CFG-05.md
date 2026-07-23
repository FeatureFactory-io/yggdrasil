# ACT-1-CFG-05 — ratatosk doctor validates config and connectivity

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-config.feature`

## Scenario (Gherkin)
```gherkin
When Priya runs "ratatosk doctor --repo ./repo"
Then exit 0, output contains "Yggdrasil MCP" and "config merge"
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | doctor command | New subcommand |
| `ratatosk/mcp_client.py` | ping | Health check |

## Do Not Do
Inherit SHARED-CONTRACT — doctor read-only; no graph writes.

## SAO.md Sections That Apply
- A7.7 ratatosk doctor future command

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_doctor_prints_merge_and_mcp` | integration Click | stdout substrings |
| `test_doctor_fails_on_bad_mcp` | integration | non-zero when unreachable |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| doctor | run | merged_config_keys, mcp_reachable |

## MCP Tools to Expose
Optional lightweight `health` or list_stereotypes ping.

## Implementation Steps
1. Add Click doctor command.
2. Print merged config summary (mask secrets).
3. Ping Yggdrasil MCP with PAT from env.

## Checkpoint
`pytest ratatosk/tests/test_cli_click.py::test_doctor_prints_merge_and_mcp -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
