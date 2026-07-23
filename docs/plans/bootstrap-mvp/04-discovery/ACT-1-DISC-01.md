# ACT-1-DISC-01 — Fixture repo discovers all manifest elements under Metamodel c4

**Tier:** 1
**Wave:** W4
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-DISC-02, MCP-PROPOSE-CHANGESET
**Blocks:** ACT-1-CLI-01, ACT-1-CLI-07, ACT-1-LLM-03

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-01 Fixture repo discovers all manifest elements under Metamodel c4
  ...
  Then bootstrap candidates include all manifest elements:
    | name           | stereotype | package     |
    | Payment API    | container  | technology  |
    | Order Service  | container  | technology  |
    | Order Domain   | component  | application |
    | Billing Worker | component  | application |
  And a ChangeSet with source "ratatosk" exists
```

---

## Why this scenario matters

This is the **discovery correctness anchor**: four named C4 elements from `sample_webapp` must appear as bootstrap candidates and enter the model only via a `ratatosk`-sourced ChangeSet. Everything else in Act 1 (CLI stdout, MCP query, Munin links) assumes this manifest passes.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | all | Ground-truth manifest |
| `src/yggdrasil/ratatosk/agent.py` | 527–650 | `bootstrap_repository` orchestration |
| `ratatosk/discovery/runner.py` | extract | LLM/scripted candidate emission |
| `src/yggdrasil/ratatosk/handoff.py` | LocalOrmHandoffPort | In-process handoff for AT |
| `docs/features/steps/discovery_steps.py` | manifest table | TFK-07 table step |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT hardcode Payment API only — all four manifest rows required.
- Do NOT write Elements without ChangeSetItem (see DISC-06).

---

## SAO.md Sections That Apply

- §17.3 bootstrap — extract element candidates
- §17 Field specialist — Ratatosk NER only

---

## Current State Assessment

| Piece | State |
|-------|--------|
| ScriptedDiscoveryLLM | Returns manifest-aligned JSON in tests |
| Manifest assertion step | Partial in behave |
| All 4 elements in candidates | Verify against current runner — may pass with scripted |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc01_all_manifest_elements_in_candidates` | integration | 4 names in bucket to_add |
| `test_disc01_changeset_source_ratatosk` | integration | ChangeSet.source == ratatosk |
| `test_disc01_stereotype_package_pairs` | integration | table columns match |
| `test_disc01_behave_manifest_table` | behave | full Gherkin |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| extract step | exit | candidate_count, manifest_names_matched |
| handoff propose | entry | op_count, model_slug |
| bootstrap_repository | exit | changeset_id, to_add_count |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `propose_changeset` | Persists candidates (in-process port calls service directly) |

---

## Implementation Steps

1. **Red:** Integration test loads manifest YAML, asserts 4/4 in candidates post-run.
2. **Green:** Fix extract/parser if any manifest row missing (stereotype normalization).
3. **Green:** Assert ChangeSet with source ratatosk exists.
4. **Green:** Behave table step compares case-insensitive stereotype/package.
5. **Refactor:** Single `assert_manifest_candidates(blackboard, yaml_path)` helper.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc01_all_manifest_elements_in_candidates -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya runs ratatosk bootstrap against the fixture repository "{name}"` | `discovery_steps.py` |
| `Then bootstrap candidates include all manifest elements:` | `discovery_steps.py` |
| `And a ChangeSet with source "ratatosk" exists` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
