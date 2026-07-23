# ACT-1-DISC-06 — Bootstrap never writes Elements outside a ChangeSet

**Tier:** 1
**Wave:** W4
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-DISC-01, ChangeSet models
**Blocks:** W0 journey certification

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-06 Bootstrap never writes Elements outside a ChangeSet
  ...
  Then a ChangeSet with source "ratatosk" exists
  And every new Element is referenced by an operation on that ChangeSet
  And there are no orphan Elements without a ChangeSetItem
```

---

## Why this scenario matters

Core **ChangeSet invariant** test — the #1 architectural rule in SHARED-CONTRACT. Catches regressions where discovery or handoff creates Element rows without ChangeSetItem linkage (ORM shortcut, partial auto-apply bug).

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/changeset/models.py` | ChangeSetItem | FK to Element ops |
| `src/yggdrasil/graph/models.py` | Element | Orphan detection query |
| `tests/integration/test_journey_bootstrap_then_update.py` | 48–117 | L1 orphan assertion pattern |
| `src/yggdrasil/changeset/services.py` | apply | Auto-apply must still create items |

---

## Do Not Do

Inherit SHARED-CONTRACT — **never bypass ChangeSet**.

---

## SAO.md Sections That Apply

- ChangeSet invariant (all writes through pipeline)

---

## Current State Assessment

Journey test may already assert orphan count — DISC-06 makes scenario explicit in behave layer.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc06_no_orphan_elements_after_bootstrap` | integration | LEFT JOIN query returns 0 orphans |
| `test_disc06_every_element_has_changeset_item` | integration | all new elements referenced |
| `test_disc06_behave` | behave | orphan step phrase |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ChangeSetService.propose` | apply each op | element_id, item_id |
| bootstrap exit | invariant check | orphan_count=0 |

---

## MCP Tools to Expose

Not applicable — DB invariant.

---

## Implementation Steps

1. **Red:** Query orphans after bootstrap — must be 0.
2. **Green:** Fix any direct Element.objects.create in discovery path.
3. **Green:** Shared test helper `assert_no_orphan_elements(model)`.
4. **Green:** Behave step wraps helper.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc06_no_orphan_elements_after_bootstrap -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `And there are no orphan Elements without a ChangeSetItem` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
