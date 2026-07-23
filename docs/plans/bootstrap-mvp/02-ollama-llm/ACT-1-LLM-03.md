# ACT-1-LLM-03 — Ollama bootstrap discovers all manifest elements

**Tier:** 1
**Wave:** W3
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `02-ollama-llm/`
**Depends on:** ACT-1-LLM-01, ACT-1-DISC-01 path
**Blocks:** ACT-1-CLI-01 (real LLM certification)

---

## Scenario (Gherkin)

```gherkin
@wip @ollama
Scenario: ACT-1-LLM-03 Ollama bootstrap discovers all manifest elements
  ...
  Then bootstrap candidates include all manifest elements:
    | Payment API | container | technology |
    | Order Service | container | technology |
    | Order Domain | component | application |
    | Billing Worker | component | application |
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | all | Ground truth for assert |
| `tests/fixtures/repos/sample_webapp/README.md` | all | Human-readable path → element map |
| `ratatosk/discovery/runner.py` | extract | Prompt must constrain to metamodel stereotypes/packages |
| `ratatosk/discovery/prompts.py` | all | Identity + JSON schema instructions |

---

## Do Not Do

Do NOT pass AT by lowering manifest to 1 element. Do NOT use scripted LLM for this scenario.

---

## Current State Assessment

- Scripted path returns 4/4 via `scripted_llm.py`.
- Real qwen3:14b may hallucinate extra elements or miss Billing Worker — prompt tuning is part of implementation, not scenario change.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_llm03_manifest_four_elements_subprocess` | integration `@ollama` | propose payload contains 4 names |
| `test_extract_prompt_lists_allowed_stereotypes` | unit | prompt includes Container, Component from MCP |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| runner extract | parse ok | candidate_count, names slug list |
| runner extract | manifest miss | missing_names list |

---

## Implementation Steps

1. Ensure project_map reads docker-compose, order_service, billing_worker paths (DISC-02 overlap).
2. Strengthen extract prompt with manifest-style JSON schema + metamodel guidance from DISC-16.
3. Run manual certification: `LLM_PROVIDER=ollama ratatosk bootstrap tests/fixtures/repos/sample_webapp ...`
4. Iterate prompt in `ratatosk/discovery/prompts.py` until 4/4 stable across 3 runs.

---

## Checkpoint

```bash
pytest -m ollama tests/integration/test_ollama_bootstrap_manifest.py -x
```

(Create dedicated integration test file during implementation.)

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
