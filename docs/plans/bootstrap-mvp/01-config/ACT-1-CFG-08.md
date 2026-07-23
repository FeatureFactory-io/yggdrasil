# ACT-1-CFG-08 — Default LLM model is qwen3:14b when unset

**Tier:** 1
**Wave:** W1
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-config.feature`
**Package:** `01-config/`
**Depends on:** ACT-1-CFG-06
**Blocks:** ACT-1-LLM-03

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CFG-08 Default LLM model is qwen3:14b when unset
  When Ratatosk loads configuration for bootstrap
  Then the effective config key "llm_ollama_model" is "qwen3:14b"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/llm/adapters/ollama.py` | 15–25 | Default model constant should be `qwen3:14b` |
| `.env.example` | LLM_OLLAMA_MODEL | Document default |
| `ratatosk/config.py` | *(create)* | Default when env unset |

---

## Do Not Do

Do NOT change default to a model not documented in PRD/user journey without human approval. Do NOT require model in repo `ratatosk.yaml` for bootstrap MVP.

---

## Current State Assessment

- Adapter default already aligned to `qwen3:14b` in recent spec pass.
- Config loader must expose key for behave; CLI must pass model to Ollama API `/api/chat` body.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_load_config_default_llm_ollama_model` | unit | unset env → `qwen3:14b` |
| `test_load_config_override_llm_ollama_model` | unit | `LLM_OLLAMA_MODEL` wins |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `OllamaClient.complete` | before request | model id, message count (not full prompt) |

---

## Implementation Steps

1. Red test for default model on config loader.
2. Green: `llm_ollama_model = env.get("LLM_OLLAMA_MODEL", "qwen3:14b")`.
3. Wire behave step with empty env override.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_config_loader.py::test_load_config_default_llm_ollama_model -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
