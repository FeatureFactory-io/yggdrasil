# ACT-1-DISC-16 — Metamodel guidance step is recorded on blackboard

**Tier:** 1
**Wave:** W4
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ACT-1-DISC-15, C4 seed
**Blocks:** DISC-04 cleanup context

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-16 Metamodel guidance step is recorded on blackboard
  ...
  Then the run blackboard contains step "metamodel_guidance"
  And the run blackboard metamodel_guidance mentions stereotype "Container"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/ratatosk/agent.py` | `_metamodel_guidance` | Text appended to LLM user message |
| `ratatosk/discovery/runner.py` | guidance step | Record on blackboard before extract |
| `src/yggdrasil/graph/` | C4 stereotypes | Container in catalog |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT put full metamodel JSON in blackboard — store summary snippet only.
- Do NOT invent stereotypes in guidance text.

---

## SAO.md Sections That Apply

- A1.3 metamodel guidance in user message

---

## Current State Assessment

Guidance generation may exist; blackboard step `metamodel_guidance` **may be missing**.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc16_blackboard_metamodel_guidance_step` | integration | step key present |
| `test_disc16_guidance_mentions_container` | integration | substring Container |
| `test_disc16_behave` | behave | Gherkin |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| metamodel guidance | built | stereotype_count, mentions_container=true |
| blackboard | record | guidance_chars |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `list_stereotypes` | Source for guidance text in MCP path |

---

## Implementation Steps

1. After loading c4 metamodel, build guidance string.
2. Set `blackboard["metamodel_guidance"]` and append step name.
3. Red/blackboard tests.
4. Ensure guidance runs before extract in step order.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc16_blackboard_metamodel_guidance_step -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `And the run blackboard metamodel_guidance mentions stereotype "{name}"` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
