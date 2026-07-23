# MCP-RECORD-RATOSK-RUN — Persist bootstrap blackboard and run linkage

**Tier:** 1
**Wave:** W2
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature` (DISC-21)
**Package:** `05-mcp-handoff/`
**Depends on:** MCP-PROPOSE-CHANGESET, `RataskRun` model
**Blocks:** ACT-1-CLI-01 (run URL), ACT-5-MCP-QUERY-10

---

## Scenario (Gherkin excerpt)

```gherkin
Then MCP tool "record_ratatosk_run" was called during bootstrap
```

---

## Why this scenario matters

Every bootstrap must leave an **auditable RataskRun** with blackboard (tree, ModelSummary, buckets) linked to the ChangeSet. Priya's CLI prints a run result URL from this record; MCP clients list history via `list_ratatosk_runs`.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/propose.py` | 156–220 | `record_ratatosk_run` tool |
| `src/yggdrasil/ratatosk/models.py` | RataskRun | Blackboard JSON field |
| `src/yggdrasil/ratatosk/handoff.py` | record_run | Port method |
| `ratatosk/discovery/runner.py` | exit | Builds blackboard dict |
| `src/yggdrasil/web/urls.py` | ratatosk-run | URL for CLI output |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT store raw PAT or LLM prompts in blackboard.
- Do NOT create RataskRun without linking changeset_id when handoff succeeded.

---

## SAO.md Sections That Apply

- §17.3 bootstrap — run history
- §18.4 tool inventory

---

## Current State Assessment

| Piece | State |
|-------|--------|
| `record_ratatosk_run` tool | Likely stub or partial |
| Blackboard schema | tree, extract, model_summary keys from runner |
| Run URL in CLI | **Gap** — CLI-01 |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_record_ratatosk_run_persists_blackboard` | integration | JSON keys preserved |
| `test_record_ratatosk_run_links_changeset` | integration | FK changeset_id set |
| `test_record_ratatosk_run_returns_run_id` | integration | id for URL construction |
| `test_record_run_mcp_harness` | harness | HTTP round-trip |
| `test_disc21_spy_record_called` | integration subprocess | call order after propose |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `record_ratatosk_run` | entry | model_slug, run_id, trigger=bootstrap, changeset_id |
| `record_ratatosk_run` | blackboard | step_keys, blackboard_size_bytes |
| `record_ratatosk_run` | exit | ratatosk_run_pk, status |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `record_ratatosk_run` | RataskRun ORM create | Yes |

---

## Implementation Steps

1. **Red:** Integration test creates run with sample blackboard.
2. **Green:** Implement tool — validate model exists, serialize blackboard.
3. **Green:** Return `{run_id, url}` for CLI printing.
4. **Green:** DISC-21 spy asserts call after propose_changeset.
5. **Refactor:** Shared blackboard schema docstring in runner.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_propose_changeset.py -k record -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Then MCP tool "record_ratatosk_run" was called during bootstrap` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
