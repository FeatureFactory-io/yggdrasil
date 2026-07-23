# ACT-1-DISC-08 — Read-only token fails before write handoff

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** MCP-PROPOSE-CHANGESET auth
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-08 Read-only token fails before write handoff
  ...
  Then the exit code is not 0
  And the output contains "permission"
  And no ChangeSet with source "ratatosk" was created for this run
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/propose.py` | auth | Read-only → PermissionError |
| `src/yggdrasil/auth/` | PAT scopes | read-only token fixture |
| `ratatosk/mcp_client.py` | error map | Surface permission to CLI stderr |

---

## Do Not Do

Inherit SHARED-CONTRACT — fail before any graph write.

---

## SAO.md Sections That Apply

- §18.5 Auth — read-only token → PermissionError before write

---

## Current State Assessment

Verify propose_changeset rejects read-only at MCP layer; CLI must not create partial state.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc08_readonly_token_exit_nonzero` | integration | exit ≠ 0, permission in output |
| `test_disc08_no_ratatosk_changeset_created` | integration | count ChangeSet source=ratatosk unchanged |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| propose_changeset | auth reject | token_scope=read_only, reason=permission |
| cli bootstrap | handoff fail | no_changeset_created=true |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `propose_changeset` | Must 403 read-only |

---

## Implementation Steps

1. Fixture read-only PAT in tests.
2. Run bootstrap through handoff boundary.
3. Assert zero new ChangeSets.
4. Map MCP 403 to CLI message containing `permission`.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc08_readonly_token_exit_nonzero -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given ... personal access token with read-only scope` | `auth_steps.py` |
| `And no ChangeSet with source "ratatosk" was created for this run` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
