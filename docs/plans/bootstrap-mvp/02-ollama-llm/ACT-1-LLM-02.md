# ACT-1-LLM-02 — Bootstrap fails clearly when Ollama model is not pulled

**Tier:** 3
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `02-ollama-llm/`
**Depends on:** ACT-1-LLM-01
**Blocks:** —

---

## Scenario (Gherkin)

```gherkin
Given Ollama is reachable at "http://localhost:11434"
And Ollama model "qwen3:14b" is not available
And the environment variable "LLM_PROVIDER" is set to "ollama"
When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
Then the exit code is not 0
And the output contains "model"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/llm/adapters/ollama.py` | complete | Ollama returns 404 when model missing — map to `LLMError` |
| `ratatosk/cli.py` | bootstrap except | Must exit non-zero with message to stderr |
| `ratatosk/discovery/runner.py` | LLM calls | Propagate error, no empty plan invent |

---

## Do Not Do

Do NOT fall back to scripted. Do NOT create empty ChangeSet with invented elements.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_ollama_complete_model_not_found_message` | unit | Error text mentions model |
| `test_cli_bootstrap_exit_nonzero_on_llm_error` | Click | exit != 0, stderr contains "model" |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `OllamaClient.complete` | 404 | reason=model_not_found, model_id |
| `ratatosk.cli.bootstrap` | except | error_class, exit_code |

---

## Implementation Steps

1. Parse Ollama error JSON on missing model.
2. Raise `LLMError` with user-facing message suggesting `ollama pull qwen3:14b`.
3. CLI catches, logs, echo stderr, exit 1.

---

## Checkpoint

```bash
pytest src/yggdrasil/llm/tests/test_ollama_client.py::test_ollama_complete_model_not_found_message -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
