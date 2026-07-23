# ACT-1-LLM-04 — Markdown-wrapped JSON extract is parsed and constrained

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `02-ollama-llm/`
**Depends on:** ACT-1-DISC-04 (same stereotype filter logic)
**Blocks:** —

---

## Scenario (Gherkin)

```gherkin
Given the discovery LLM will return a candidate with stereotype "microservice"
When Priya runs ratatosk bootstrap against the fixture repository "sample_webapp"
Then no ChangeSet operation references stereotype "microservice"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/ratatosk/agent.py` | extract parse | `_parse_llm_json`, stereotype cleanup |
| `ratatosk/discovery/runner.py` | extract | Same cleanup for CLI path |
| `ratatosk/discovery/scripted_llm.py` | inject bad | Test double for AT |

---

## Do Not Do

Do NOT add "microservice" to C4 metamodel. Do NOT silently coerce to Container without logging drop.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_parse_fenced_json_markdown` | unit | ```json block parsed |
| `test_drop_unknown_stereotype_before_propose` | integration | op list excludes microservice |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| cleanup | stereotype rejected | candidate name, invalid stereotype, allowed set |

---

## Implementation Steps

1. Share JSON fence stripper between agent and runner.
2. Filter candidates against MCP `list_stereotypes` slugs before bucket reconcile.
3. Scripted LLM hook for AT injects bad stereotype.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_drop_unknown_stereotype -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
