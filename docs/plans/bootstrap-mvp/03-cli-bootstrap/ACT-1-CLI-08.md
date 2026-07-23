# ACT-1-CLI-08 — Empty model bootstrap runs wipe no-op then scan

**Tier:** 1
**Wave:** W5
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** W0 foundation, ACT-1-DISC-06 (orphan invariant)
**Blocks:** ACT-1-CLI-01, ACT-1-CLI-02

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-08 Empty model bootstrap runs wipe no-op then scan
  ...
  Then the exit code is 0
  And the output contains wipe no-op for empty graph
  And the output contains "building ModelSummary"
  And the output contains "to_add:"
```

---

## Why this scenario matters

Bootstrap policy (SAO §17.3, SHARED-CONTRACT) requires a **wipe step before every bootstrap scan**. On an empty model this must be a fast no-op with explicit messaging — not skipped silently. That message becomes the regression guard against accidentally skipping wipe on populated models (CLI-02).

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | 80–150 | Insert wipe call before ModelSummary |
| `src/yggdrasil/ratatosk/agent.py` | 527–600 | In-process `bootstrap_repository` wipe reference |
| `ratatosk/mcp_client.py` | wipe helper | MCP `bulk_wipe_model` or propose delete-all — follow SAO |
| `tests/fixtures/repos/sample_webapp/` | all | Empty-model fixture target |
| `docs/features/steps/cli_steps.py` | wipe step | `wipe no-op for empty graph` phrase |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT skip wipe when element count is 0 — still log no-op.
- Do NOT delete the `YggdrasilModel` row or metamodel binding — Elements + Relationships only.
- Do NOT use ORM wipe from CLI — MCP server owns graph mutations.

---

## SAO.md Sections That Apply

- §17.3 bootstrap flow — bulk wipe before rescan
- ChangeSet invariant — wipe ops auditable when non-empty (CLI-02)

---

## Current State Assessment

| Piece | State |
|-------|--------|
| Wipe step in runner | **Missing** — scan starts without wipe |
| Empty-graph no-op message | **Missing** |
| MCP bulk wipe tool | Verify existence or add via propose batch |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_bootstrap_empty_model_wipe_noop_message` | integration | stdout contains exact no-op phrase |
| `test_bootstrap_empty_model_no_elements_before_scan` | integration | element count 0 before and after wipe step |
| `test_bootstrap_still_discovers_candidates` | integration | `to_add:` > 0 after scan |
| `test_cli08_behave` | behave | Gherkin wipe no-op step |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `run_cli_discovery` | wipe entry | model_slug, element_count, relationship_count |
| `run_cli_discovery` | wipe no-op | reason=empty_graph, duration_ms |
| `run_cli_discovery` | wipe bulk | deleted_elements, deleted_relationships (CLI-02 path) |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `bulk_wipe_model` or equivalent | Server-side wipe; CLI calls via MCP only |

If tool missing, plan MCP-PROPOSE-CHANGESET wipe batch — document in handoff package.

---

## Implementation Steps

1. **Red:** Test expects `wipe no-op for empty graph` — fails today.
2. **Green:** Query model stats via MCP before scan; if both counts 0, log/print no-op phrase.
3. **Green:** Proceed to ModelSummary + scan unchanged.
4. **Green:** Ensure wipe runs **before** `building ModelSummary` log order.
5. **Refactor:** Extract `_wipe_or_noop(model_slug)` in runner ≤25 lines.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_bootstrap_empty_model_wipe_noop_message -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Then the output contains wipe no-op for empty graph` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
