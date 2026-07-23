# ACT-1-DISC-14 — Non-JSON LLM plan does not invent hardcoded Elements

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-14 Non-JSON LLM plan does not invent hardcoded Elements
  Given ... discovery LLM returns non-JSON prose only
  ...
  Then the exit code is 0
  And the output contains "no architecture changes detected" or "empty plan"
  And there are no orphan Elements without a ChangeSetItem
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | parse | Handle parse failure gracefully |
| `ratatosk/discovery/scripted_llm.py` | hook | Return prose fixture |
| `src/yggdrasil/ratatosk/handoff.py` | allow_empty | Empty propose path |

---

## Do Not Do

Inherit SHARED-CONTRACT — no Payment API fallback on parse failure.

---

## SAO.md Sections That Apply

- §17.3 — empty plan is valid outcome

---

## Current State Assessment

Parser may throw or invent — must exit 0 with empty plan message.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc14_non_json_empty_plan_message` | integration | stdout phrase |
| `test_disc14_no_elements_created` | integration | element count 0 |
| `test_disc14_allow_empty_changeset_or_skip_propose` | integration | no orphan |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| extract parse | fail | reason=non_json, action=empty_plan |
| handoff | skip or empty | allow_empty=true |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `propose_changeset` | `allow_empty=true` when zero ops |

---

## Implementation Steps

1. Scripted LLM returns prose only.
2. Runner catches parse error → empty candidates.
3. Print user-facing empty plan message.
4. Or skip propose with record_run status complete.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc14_non_json_empty_plan_message -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the discovery LLM returns non-JSON prose only` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
