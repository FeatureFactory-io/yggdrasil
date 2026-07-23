# ACT-1-CLI-01 — Generic bootstrap creates a ChangeSet from repository scan

**Tier:** 1
**Wave:** W5
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** ACT-1-DISC-01, ACT-1-CLI-08, ACT-1-DISC-21, ACT-1-CFG-09
**Blocks:** ACT-1-CLI-07, ACT-5-MCP-QUERY-01

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-01 Generic bootstrap creates a ChangeSet from repository scan
  Given Priya has a Yggdrasil personal access token with read-write scope
  And the Yggdrasil model "Yggdrasil" exists with no elements
  And the fixture repository "sample_webapp" is available
  And the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
  When Priya runs:
    """
    ratatosk bootstrap ./repo --token=$YGGDRASIL_TOKEN --model Yggdrasil --metamodel=c4 \
      --server $YGGDRASIL_SERVER_URL
    """
  Then the exit code is 0
  And the output contains "building ModelSummary"
  And the output contains "scanning"
  And the output contains "to_add:"
  And the output contains "run complete"
  And the output contains "ChangeSet #"
  And the output contains "pending"
  And a link to the run result is printed
```

---

## Why this scenario matters

This is the **certification scenario** for Act 1: Priya runs one command from her laptop and gets a traceable Ratatosk run plus ChangeSet without opening the browser. It proves the full subprocess boundary — Click CLI → Django-free runner → HTTP MCP handoff — not just in-process AT.

The stdout phrases are a **contract**: they must match user_journey Act 1 transcript (`building ModelSummary`, not legacy `fetching existing model state`). The `pending` line reflects auto-apply policy: high-confidence ops apply; any below 0.80 remain pending (see SHARED-CONTRACT).

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 75–130 | `bootstrap` command — orchestrates client + runner |
| `ratatosk/discovery/runner.py` | 51–120 | Log phrases for ModelSummary, scan, buckets |
| `ratatosk/mcp_client.py` | all | HTTP transport to `/mcp/tools/` |
| `src/yggdrasil/ratatosk/handoff.py` | 148–222 | Reference for handoff response shape |
| `tests/integration/test_journey_bootstrap_then_update.py` | 48–117 | L1 pattern — extend with subprocess variant |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT call `django.setup()` in the CLI bootstrap path.
- Do NOT assert exact ChangeSet id or op count in stdout — use `ChangeSet #` pattern only.
- Do NOT require manual `approve_changeset` on happy path when all ops ≥0.80 confidence.

---

## SAO.md Sections That Apply

- §17.3 Ratatosk bootstrap flow — wipe → ModelSummary → extract → Munin handoff
- §18.4 Tool inventory — `propose_changeset`, `record_ratatosk_run`
- §18.5 Auth — Bearer PAT on MCP transport

---

## Current State Assessment

| Piece | State |
|-------|--------|
| Click `bootstrap` command | Exists — token optional until `_require_token` |
| Runner log `building ModelSummary` | **Gap** — still logs `fetching existing model state` |
| Subprocess test with MCP spy | **Partial** — DISC-21 covers tool calls; CLI-01 adds stdout contract |
| Run result URL in output | **Gap** — need stable URL template to RATATOSK_RUN view |
| `pending` in output when auto-applied | **Design** — show pending count for sub-threshold ops only |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_cli_bootstrap_happy_path_stdout` | integration subprocess | All required stdout substrings present |
| `test_cli_bootstrap_exit_zero` | integration | exit 0 with sample_webapp fixture |
| `test_cli_bootstrap_prints_changeset_id` | integration | output matches `ChangeSet #\d+` |
| `test_cli_bootstrap_prints_run_url` | integration | URL contains run id or `/ratatosk-run/` path |
| `test_cli01_behave_subprocess` | behave | Full Gherkin table via TFK-07 |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ratatosk.cli.bootstrap` | entry | repo_path, model_name, metamodel, server_url (no token) |
| `run_cli_discovery` | ModelSummary start | step=building_model_summary, model_slug |
| `run_cli_discovery` | scan start | repo_path, file_count |
| `run_cli_discovery` | bucket summary | to_add, to_update, to_delete counts |
| `McpHandoffPort.propose` | exit | changeset_id, applied_count, pending_count |
| `ratatosk.cli.bootstrap` | exit | exit_code, run_id, changeset_id |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `ensure_model` | Called before handoff |
| `list_stereotypes` | Metamodel guidance |
| `propose_changeset` | Element ops + Munin enrichment |
| `record_ratatosk_run` | Blackboard + run URL source |

---

## Implementation Steps

1. **Red:** Subprocess test expecting `building ModelSummary` — fails on current log text.
2. **Green:** Rename runner log phrase to `building ModelSummary` (align DISC-15/CLI-08).
3. **Green:** Emit bucket lines `to_add: N` after reconcile in runner stdout handler.
4. **Green:** After handoff, print `run complete`, `ChangeSet #<id>`, pending count from response.
5. **Green:** Print run result URL from `record_ratatosk_run` response or constructed from run_id.
6. **Refactor:** Centralize stdout formatting in `ratatosk/output.py` for testability.
7. **TFK07:** Wire multi-line `When Priya runs:` step with env substitution.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_cli_bootstrap_happy_path_stdout -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya runs:` (multiline command) | `cli_steps.py` |
| `Then the output contains "{text}"` | `cli_steps.py` |
| `And a link to the run result is printed` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc (real MCP test server)
- do-write-concise-methods.mdc
- do-informative-logging.mdc
