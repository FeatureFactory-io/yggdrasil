# ACT-1-DISC-13 — MCP snapshot failure does not fall back to silent ORM invent

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-13 MCP snapshot failure does not fall back to silent ORM invent
  Given ... MCP snapshot endpoint is unreachable
  ...
  Then the exit code is not 0
  And the output contains "MCP"
  And there are no orphan Elements without a ChangeSetItem
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/mcp_client.py` | errors | No fallback to django.setup |
| `ratatosk/discovery/runner.py` | snapshot | Model state via MCP only |
| SHARED-CONTRACT | ORM | No CLI ORM writes |

---

## Do Not Do

Inherit SHARED-CONTRACT — **never** silent ORM invent on MCP failure.

---

## SAO.md Sections That Apply

- §1 Dependency rules — remote MCP client

---

## Current State Assessment

Verify no code path calls `LocalOrmHandoffPort` from production CLI on MCP error.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc13_mcp_unreachable_fails_loudly` | integration | exit ≠ 0, MCP in output |
| `test_disc13_no_orphans_on_failure` | integration | orphan count 0 |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| McpClient | connection fail | endpoint, error_class |
| runner | abort | reason=mcp_snapshot_failed, no_orm_fallback=true |

---

## MCP Tools to Expose

Simulate failure on `list_elements` or snapshot tool used pre-handoff.

---

## Implementation Steps

1. Harness returns 503 for snapshot tool.
2. Assert CLI fails with MCP message.
3. Assert no Element rows created.

---

## Checkpoint

```bash
pytest tests/integration/mcp_harness/test_disc13_mcp_unreachable.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the MCP snapshot endpoint is unreachable` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
