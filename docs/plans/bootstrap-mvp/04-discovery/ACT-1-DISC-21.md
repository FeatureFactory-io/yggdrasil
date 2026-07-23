# ACT-1-DISC-21 — Subprocess bootstrap calls MCP handoff tools

**Tier:** 1
**Wave:** W4 (after W2)
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** MCP-PROPOSE-CHANGESET, MCP-RECORD-RATOSK-RUN, ACT-1-CFG-09
**Blocks:** ACT-1-CLI-09, ACT-1-LLM-01

---

## Scenario (Gherkin)

```gherkin
@wip
Scenario: ACT-1-DISC-21 Subprocess bootstrap calls MCP handoff tools
  ...
  When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
  Then MCP tool "ensure_model" was called during bootstrap
  And MCP tool "list_stereotypes" was called during bootstrap
  And MCP tool "propose_changeset" was called during bootstrap
  And MCP tool "record_ratatosk_run" was called during bootstrap
```

---

## Why this scenario matters

Bridges **in-process discovery proofs** to **production CLI transport**. Spy or mock MCP server records tool names in call order — proves RatatoskMcpClient wiring without django.setup in subprocess.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/mcp_client.py` | call_tool | HTTP POST each tool |
| `tests/integration/mcp_harness/` | spy server | Records tool invocations |
| `docs/plans/bootstrap-mvp/00-foundation/TFK07-AT-STEPS.md` | subprocess | Fixture pattern |
| `ratatosk/cli.py` | bootstrap | End-to-end entry |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT use LocalOrmHandoffPort in subprocess test.
- Do NOT require live Ollama — scripted LLM OK for tool-order test.

---

## SAO.md Sections That Apply

- §18.4 tool inventory
- §1 Dependency rules — remote client

---

## Current State Assessment

MCP harness may exist from W2; subprocess wrapper **needs TFK-07** `via subprocess` step.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc21_subprocess_mcp_tool_calls` | integration | 4 tool names in call log |
| `test_disc21_call_order_propose_before_record` | integration | ordering |
| `test_disc21_behave` | behave | @wip scenario |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `RatatoskMcpClient.call_tool` | each call | tool_name, duration_ms |
| mcp harness | receive | tool_name, sequence_index |

---

## MCP Tools to Expose

All four must be registered on test server: `ensure_model`, `list_stereotypes`, `propose_changeset`, `record_ratatosk_run`.

---

## Implementation Steps

1. Extend mcp_harness with call recorder middleware.
2. Subprocess bootstrap against harness URL.
3. Assert four tool names present.
4. TFK-07 subprocess step with env for server URL.

---

## Checkpoint

```bash
pytest tests/integration/mcp_harness/test_subprocess_bootstrap_tools.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya runs ratatosk bootstrap against fixture "{name}" via subprocess` | `discovery_steps.py` |
| `Then MCP tool "{name}" was called during bootstrap` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc (real HTTP to harness)
- do-informative-logging.mdc
