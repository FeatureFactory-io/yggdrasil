# ACT-5-MCP-QUERY-10 — list_ratatosk_runs returns run history

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** MCP-RECORD-RATOSK-RUN, multiple completed runs

---

## Scenario (Gherkin)

```gherkin
Given model has 3 completed Ratatosk runs
When CI agent calls list_ratatosk_runs model Yggdrasil
Then 3 runs, run id=3 complete with changeset_id=1
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | list_ratatosk_runs | May be missing |
| `src/yggdrasil/ratatosk/models.py` | RataskRun | status, changeset FK |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- §18.4 run history tools

---

## Current State Assessment

Tool may be unregistered — implement with record_ratatosk_run data.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_ratatosk_runs_three` | integration | count + id=3 metadata |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_ratatosk_runs` | exit | model, run_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `list_ratatosk_runs` | RatatoskRunQueryService.list | No |

---

## Implementation Steps

1. Register tool on MCP server.
2. Seed 3 RataskRun rows.
3. Red/green + behave.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_ratatosk_runs_three -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
