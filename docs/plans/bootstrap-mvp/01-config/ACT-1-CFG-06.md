# ACT-1-CFG-06 — LLM_PROVIDER ollama selects Ollama not scripted fallback

**Tier:** 1
**Wave:** W1
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-config.feature`
**Package:** `01-config/`
**Depends on:** W0 (TFK07 config steps)
**Blocks:** ACT-1-LLM-01, ACT-1-LLM-03, ACT-1-CFG-07, ACT-1-CFG-08

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CFG-06 LLM_PROVIDER ollama selects Ollama not scripted fallback
  Given the environment variable "LLM_PROVIDER" is set to "ollama"
  When Ratatosk loads configuration for bootstrap
  Then the effective config key "llm_provider" is "ollama"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 38–53 | `_build_llm()` today treats empty provider as scripted — **violates CFG-06** |
| `ratatosk/cli.py` | 90 | bootstrap calls `_build_llm()` without config module |
| `src/yggdrasil/llm/adapters/ollama.py` | 1–40 | `OllamaClient` constructor reads env — should receive config object |
| `docs/features/steps/cli_steps.py` | TFK07 stub | `When Ratatosk loads configuration for bootstrap` |
| `tests/fixtures/repos/sample_webapp/ratosk.yaml` | all | Repo-level config stub for merge order tests later |

---

## Do Not Do

Inherit [SHARED-CONTRACT.md](../00-foundation/SHARED-CONTRACT.md), plus:

- Do NOT import Django in `ratatosk/config.py`.
- Do NOT silently fall back to `ScriptedDiscoveryLLM` when `LLM_PROVIDER=ollama` — fail fast if Ollama client cannot be constructed.
- Do NOT read config only in bootstrap — `update` must use same loader.

---

## SAO.md Sections That Apply

- §17.6 Model tiers — Ratatosk field tier via Ollama locally
- §18 external integrations — CLI uses env + config, not in-process Django settings

---

## Current State Assessment

### Exists

- `LLM_PROVIDER` env var read ad hoc in `_build_llm()`.
- `ScriptedDiscoveryLLM` for CI/scripted path.

### Missing

- No `ratatosk/config.py` with merge order documented in feature file.
- Empty `LLM_PROVIDER` defaults to scripted (lines 45–46) — contradicts spec when user explicitly sets `ollama`.
- No typed `BootstrapConfig` dataclass for behave step to inspect `llm_provider`.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_load_config_llm_provider_ollama_from_env` | unit | `load_bootstrap_config(env={"LLM_PROVIDER": "ollama"}).llm_provider == "ollama"` |
| `test_build_llm_returns_ollama_client_when_configured` | unit | isinstance client, not ScriptedDiscoveryLLM |
| `test_build_llm_no_silent_fallback_when_ollama_requested` | unit | Ollama import failure raises or logs error — no scripted swap |
| `test_cfg06_behave_effective_config_key` | behave | Gherkin scenario green |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ratatosk.config.load_bootstrap_config` | entry | merge sources present (flags/env/repo/home) |
| `ratatosk.config.load_bootstrap_config` | exit | effective `llm_provider`, `ollama_base_url` (not token) |
| `ratatosk.cli._build_llm` | branch | chosen provider class name, reason if reject scripted |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. **Red:** Create `ratatosk/config.py` with `load_bootstrap_config(*, env, repo_path, flags) -> BootstrapConfig` and failing tests above.
2. **Green:** Map `LLM_PROVIDER` → `llm_provider` key; normalize to lowercase.
3. **Green:** Refactor `_build_llm(config: BootstrapConfig)` — if `ollama`, instantiate `OllamaClient(base_url=config.ollama_base_url, model=config.llm_ollama_model)`.
4. **Green:** Wire TFK07 behave step to call loader with `context.env_overrides`.
5. **Refactor:** bootstrap/update commands load config once at start; pass to discovery runner.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_config_loader.py::test_load_config_llm_provider_ollama_from_env -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the environment variable "{name}" is set to "{value}"` | `docs/features/steps/cli_steps.py` |
| `When Ratatosk loads configuration for bootstrap` | `docs/features/steps/cli_steps.py` |
| `Then the effective config key "{key}" is {value}` | `docs/features/steps/cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-small-increments.mdc
- do-write-concise-methods.mdc
- do-informative-logging.mdc
