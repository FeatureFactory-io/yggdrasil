# ACT-1-CLI-04 — Munin receives element candidates and plans relationships

**Tier:** 1
**Wave:** W6
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `06-munin-linking/`
**Depends on:** ACT-1-CLI-01, ACT-1-DISC-01
**Blocks:** ACT-5-MCP-QUERY-03, ACT-5-MCP-QUERY-04

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-04 Munin receives element candidates from bootstrap and plans relationships
  Given Ratatosk has produced bootstrap buckets:
    | bucket | count |
    | to_add | 27    |
  Then Munin produces ChangeSet with at least 27 planned operations
  And the ChangeSet summary contains "add-element ops"
  And the ChangeSet summary contains "add-relationship ops"
```

---

## Architectural gap (think first)

Ratatosk's job ends at **element NER**. Munin's job is to read those candidates and plan **relationships** (and validate metamodel) before ChangeSet persist.

**Today:** `propose_changeset` in `src/yggdrasil/mcp/tools/propose.py` calls `ChangeSetService.propose()` with Ratatosk's element ops only. No `MuninAgent` invocation. `munin_reasoning` is a static summary from Ratatosk buckets — no add-relationship ops.

**Target:** When `source=ratatosk` and bootstrap handoff includes element-only ops, server-side planner enriches operations list before propose + auto-apply.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/propose.py` | 74–164 | Hook Munin planner before `_service.propose` |
| `src/yggdrasil/munin/agent.py` | 80–200 | `MuninAgent` — reuse planning tier, not full chat loop |
| `src/yggdrasil/ratatosk/agent.py` | 745–780 | `handoff_buckets_to_munin` — AT fixture for CLI-04 table |
| `src/yggdrasil/changeset/services.py` | 62–140 | `propose()` — unchanged signature |
| `docs/features/steps/cli_steps.py` | Munin ops step | `@wip` TFK07 |
| `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | all | Expected edges for sample_webapp (extend with relationships section) |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT let Ratatosk CLI call `MuninAgent` directly — enrichment happens **inside MCP propose_changeset** on server.
- Do NOT apply relationships without ChangeSet items — same pipeline as elements.
- Do NOT hardcode 27 ops in production — scenario uses fixture table; sample_webapp expects ~4 elements + N relationships.

---

## SAO.md Sections That Apply

- §17.3 bootstrap flow — Munin plans relationships after element handoff
- §17.6 MuninAgent identity — planning tier LLM
- ChangeSet invariant

---

## Design proposal

Add `MuninBootstrapPlanner` (module `src/yggdrasil/munin/bootstrap_planner.py`):

```python
def plan_bootstrap_changeset(
    *,
    model_id: int,
    element_ops: list[dict],
    user_id: int | None,
    llm: BaseLLM | None = None,
) -> tuple[list[dict], str]:
    """Return merged ops (elements + relationships) and munin_reasoning summary."""
```

**Logic (deterministic minimum for MVP):**

1. For each add-element op, infer C4 containment/use relationships from package + stereotype rules (Order Domain component → Order Service container).
2. Optional LLM pass for ambiguous edges — use `ScriptedLLM` in tests.
3. Append `add_relationship` ops with confidence scores.
4. Build summary: `"Bootstrap handoff: N add-element ops, M add-relationship ops"`.

Invoke from `propose_changeset` when `source == ratatosk` and operations contain only element ops (no relationship ops yet).

---

## Current State Assessment

| Piece | State |
|-------|--------|
| AT step `Munin produces ChangeSet with at least N ops` | Partial — checks ChangeSet count via ORM |
| Relationship ops in propose | **Missing** |
| sample_webapp relationship manifest | **Missing** — add to YAML in implementation |
| Auto-apply 0.80 | Exists in propose.py |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_bootstrap_planner_adds_relationship_ops` | unit | 4 elements → ≥1 relationship op |
| `test_propose_changeset_ratatosk_invokes_planner` | integration T2 | munin_reasoning contains both op types |
| `test_propose_changeset_mcp_client` | T1 | schema unchanged for clients |
| `test_cli04_behave_munin_summary` | behave | table scenario with fixture buckets |
| `test_journey_traverse_after_bootstrap` | L1 extension | relationships queryable |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `MuninBootstrapPlanner.plan` | entry | model_id, element_op_count, user_id |
| `MuninBootstrapPlanner.plan` | exit | relationship_op_count, summary preview |
| `propose_changeset` | after enrich | total_ops, applied_count, pending_count |

---

## MCP Tools to Expose

| Tool | Change |
|------|--------|
| `propose_changeset` | Internal enrichment — no schema change to clients |

---

## Implementation Steps

1. **Red:** `test_bootstrap_planner_adds_relationship_ops` with 4 element dicts from manifest.
2. **Green:** Rule-based planner for sample_webapp topology (Payment API ← Order Domain, etc.).
3. **Red:** integration test propose_changeset summary contains `add-relationship`.
4. **Green:** Wire planner in `propose.py` before `_service.propose`.
5. **Green:** Extend `expected_elements.yaml` with `relationships:` section for test assertions.
6. **Green:** Behave CLI-04 with `Given Ratatosk has produced bootstrap buckets` seeding 27 synthetic ops OR scale sample_webapp scenario to realistic N.
7. **Refactor:** Keep `MuninBootstrapPlanner` ≤30 lines public method; rules in `_infer_relationships`.

---

## Checkpoint

```bash
pytest src/yggdrasil/munin/tests/test_bootstrap_handoff.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given Ratatosk has produced bootstrap buckets:` | `cli_steps.py` |
| `Then Munin produces ChangeSet with at least {n:d} planned operations` | `cli_steps.py` |
| `Then the ChangeSet summary contains "{text}"` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-write-concise-methods.mdc
- do-informative-logging.mdc
