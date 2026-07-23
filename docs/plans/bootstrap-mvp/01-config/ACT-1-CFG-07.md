# ACT-1-CFG-07 — OLLAMA_BASE_URL from env is used by CLI LLM client

**Tier:** 1
**Wave:** W1
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-config.feature`
**Package:** `01-config/`
**Depends on:** ACT-1-CFG-06
**Blocks:** ACT-1-LLM-01

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CFG-07 OLLAMA_BASE_URL from env is used by CLI LLM client
  Given the environment variable "OLLAMA_BASE_URL" is set to "http://localhost:11434"
  When Ratatosk loads configuration for bootstrap
  Then the effective config key "ollama_base_url" is "http://localhost:11434"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/llm/adapters/ollama.py` | 20–45 | Reads `OLLAMA_BASE_URL` with `LLM_OLLAMA_URL` fallback |
| `.env.example` | OLLAMA vars | Canonical name documented |
| `ratatosk/config.py` | *(create)* | Must expose `ollama_base_url` on merged config |
| `ratatosk/cli.py` | 47–50 | Pass config URL into `OllamaClient`, not raw os.environ in CLI |

---

## Do Not Do

Inherit SHARED-CONTRACT. Do NOT introduce a third env name — `OLLAMA_BASE_URL` is canonical; `LLM_OLLAMA_URL` fallback only inside adapter for backward compat.

---

## Current State Assessment

- `OllamaClient` already prefers `OLLAMA_BASE_URL` in adapter.
- CLI does not surface merged config key for behave assertion.
- Risk: CLI and adapter read env independently — config loader must be single source of truth passed into client ctor.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_load_config_ollama_base_url_from_env` | unit | effective URL from `OLLAMA_BASE_URL` |
| `test_ollama_client_uses_config_url_not_hardcoded` | unit | mock HTTP base matches config |
| `test_llm_ollama_url_fallback_when_base_unset` | unit | legacy `LLM_OLLAMA_URL` still works |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `OllamaClient.__init__` | init | resolved base_url (host only ok), model name |
| `load_bootstrap_config` | merge | source=env for ollama_base_url |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Add `ollama_base_url: str` to `BootstrapConfig` default `http://localhost:11434`.
2. Load from `OLLAMA_BASE_URL`, then fallback `LLM_OLLAMA_URL`.
3. Pass into `OllamaClient(base_url=config.ollama_base_url)`.
4. Behave step asserts `context.bootstrap_config.ollama_base_url`.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_config_loader.py::test_load_config_ollama_base_url_from_env -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
