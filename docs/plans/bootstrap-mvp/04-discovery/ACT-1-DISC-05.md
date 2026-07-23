# ACT-1-DISC-05 — Discovery uses LLM turns not hardcoded Payment API fallback

**Tier:** 3 (error hygiene)
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-DISC-01
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-05 Discovery uses LLM turns not hardcoded Payment API fallback
  ...
  When ... with a scripted discovery LLM
  Then the discovery LLM was invoked at least once
  And the run blackboard contains step "project_map"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/scripted_llm.py` | all | Legitimate scripted path — not silent hardcode |
| `ratatosk/discovery/runner.py` | project_map | LLM call site |
| SHARED-CONTRACT | Payment API | No silent hardcoded candidates except explicit scripted |

---

## Do Not Do

Inherit SHARED-CONTRACT — remove any Payment API hardcode outside `ScriptedDiscoveryLLM` when `LLM_PROVIDER=scripted`.

---

## SAO.md Sections That Apply

- §17.3 — LLM-driven extract

---

## Current State Assessment

Audit runner for hardcoded Payment API injection when LLM fails — must not exist on default path.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc05_llm_invoked_with_scripted_provider` | integration | call count ≥ 1 |
| `test_disc05_blackboard_project_map_step` | integration | step key present |
| `test_disc05_no_hardcoded_payment_without_llm` | unit | grep/static analysis test |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| project_map | LLM call | provider=scripted, turn=1 |
| runner | no hardcode path | source=llm_not_fallback |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Add injectable LLM call counter on scripted client.
2. Red test for project_map blackboard step.
3. Remove any legacy Payment API fallback in runner (if found).
4. Document scripted as explicit test/CI mode only.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc05_llm_invoked_with_scripted_provider -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When ... with a scripted discovery LLM` | `discovery_steps.py` |
| `Then the discovery LLM was invoked at least {n:d} times` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
