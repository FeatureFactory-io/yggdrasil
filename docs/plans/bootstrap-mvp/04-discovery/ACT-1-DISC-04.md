# ACT-1-DISC-04 — Cleanup drops unknown stereotype before Munin

**Tier:** 3 (error hygiene)
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-DISC-16, metamodel catalog
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-04 Cleanup drops unknown stereotype before Munin
  Given ... discovery LLM will return a candidate with stereotype "microservice"
  ...
  Then no ChangeSet operation references stereotype "microservice"
  And the model does not contain an element with stereotype "microservice"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | cleanup | Filter against metamodel stereotypes |
| `ratatosk/discovery/scripted_llm.py` | inject bad stereotype | Test hook |
| `src/yggdrasil/ratatosk/agent.py` | pre-handoff | Drop invalid candidates |

---

## Do Not Do

Inherit SHARED-CONTRACT — no silent acceptance of LLM-invented stereotypes.

---

## SAO.md Sections That Apply

- §17 Field specialist — metamodel-constrained NER

---

## Current State Assessment

Same behavior as ACT-1-LLM-04 — share cleanup module; DISC-04 uses scripted inject, LLM-04 tests markdown JSON path.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc04_drops_microservice_stereotype` | integration | 0 ops with microservice |
| `test_disc04_logs_dropped_candidate` | unit | WARNING with stereotype name |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| cleanup | drop unknown | candidate_name, stereotype, reason=not_in_metamodel |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Red with scripted LLM returning microservice candidate.
2. Green filter before propose_changeset.
3. Log dropped candidates at WARNING.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc04_drops_microservice_stereotype -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the discovery LLM will return a candidate with stereotype "{name}"` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
