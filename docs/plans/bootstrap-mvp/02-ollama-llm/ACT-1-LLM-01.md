# ACT-1-LLM-01 — Bootstrap uses Ollama when LLM_PROVIDER is ollama

**Tier:** 1
**Wave:** W3
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `02-ollama-llm/`
**Depends on:** ACT-1-CFG-06, ACT-1-CFG-07, TFK07 Ollama steps, ACT-1-DISC-21 (subprocess path)
**Blocks:** ACT-1-LLM-03

---

## Scenario (Gherkin)

```gherkin
@wip @ollama
Scenario: ACT-1-LLM-01 Bootstrap uses Ollama when LLM_PROVIDER is ollama
  Given Ollama is reachable at "http://localhost:11434"
  And the environment variable "LLM_PROVIDER" is set to "ollama"
  ...
  When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
  Then the discovery LLM was invoked at least once
  And the output does not contain "scripted-discovery"
```

---

## Why this scenario matters

CFG-06 only proves config **selection**. This scenario proves the CLI actually **calls** Ollama during discovery — the difference between "env var set" and "real bootstrap with qwen3:14b".

Today `OllamaClient.complete()` is `NotImplementedError` (line 76). `_build_llm()` also falls back to scripted when import fails — so even with `LLM_PROVIDER=ollama` users may never hit the network.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/llm/adapters/ollama.py` | 59–90 | **Implement** `complete`, `_build_payload`, `_parse_response` |
| `src/yggdrasil/llm/base.py` | 60–130 | `LLMMessage`, `LLMResponse`, `LLMError` contract |
| `ratatosk/discovery/runner.py` | 200–350 | Calls `llm.complete` for project_map + extract steps |
| `ratatosk/discovery/scripted_llm.py` | all | Reference for step sequence — Ollama must satisfy same JSON shape |
| `ratatosk/cli.py` | 38–53 | Must not fallback to scripted when ollama configured |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT use `ScriptedDiscoveryLLM` in this scenario's happy path.
- Do NOT call Ollama from Django test settings by default — unit tests use `ScriptedLLM`; mark live Ollama tests `@ollama`.
- Do NOT log full prompts or responses at INFO — log model id, token counts, latency.

---

## SAO.md Sections That Apply

- §17.6 Field tier — Ratatosk uses small/fast local model
- LLM abstraction — swap provider via config

---

## Current State Assessment

| Component | State |
|-----------|--------|
| `OllamaClient.__init__` | Done — reads model/URL |
| `OllamaClient.complete` | **NotImplementedError** |
| Runner LLM calls | Expects `complete()` returning parseable JSON for extract |
| Subprocess + spy | TFK07 not wired — need call counter on client or HTTP mock |
| `@ollama` marker | Document in pyproject for optional CI job |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_ollama_complete_posts_to_api_chat` | unit | `urllib`/`httpx` mock receives POST `/api/chat` with model field |
| `test_ollama_complete_returns_llm_response` | unit | Parses `message.content` from Ollama JSON |
| `test_ollama_complete_raises_llm_error_on_404_model` | unit | Clear error when model missing (feeds LLM-02) |
| `test_ollama_complete_raises_on_connection_refused` | unit | No silent fallback to scripted |
| `test_build_llm_invokes_ollama_when_configured` | unit | CLI factory with CFG-06 config |
| `test_llm01_subprocess_invokes_real_client` | integration `@ollama` | Optional live daemon — discovery LLM call count ≥ 1 |

Use `responses` or `httpx.MockTransport` — not live Ollama in default CI.

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `OllamaClient.complete` | entry | model_id, message_count, max_tokens |
| `OllamaClient.complete` | HTTP response | status_code, duration_ms, eval_count if present |
| `OllamaClient.complete` | LLMError | reason=connection_failed / model_not_found / bad_status |
| `ratatosk.discovery.runner` | after LLM call | step=project_map or extract, parse_status |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. **Red:** Unit test with mocked HTTP 200 and minimal Ollama chat JSON; expect `LLMResponse.content`.
2. **Green:** Implement `_build_payload`: map `LLMMessage` list + system to Ollama `messages` array; set `stream: false`.
3. **Green:** Implement `_parse_response`: read `message.content`, map usage if available.
4. **Green:** Use stdlib `urllib.request` or existing project HTTP helper — match SAO offline constraint (no new heavy deps without approval).
5. **Green:** Map `LLMError` on non-200; include response body snippet at DEBUG only.
6. **Green:** Wire CFG-06 so fallback to scripted **only** when provider unset/scripted — not when ollama selected.
7. **Refactor:** Extract `_post_json(url, payload)` private helper ≤ 20 lines.
8. **TFK07:** Implement Ollama reachable step + `discovery LLM was invoked` counter via injectable client wrapper in subprocess test.

---

## Checkpoint

```bash
pytest src/yggdrasil/llm/tests/test_ollama_client.py -x
```

Optional live:

```bash
pytest -m ollama src/yggdrasil/llm/tests/test_ollama_client.py -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given Ollama is reachable at "{url}"` | `cli_steps.py` |
| `Then the discovery LLM was invoked at least {n:d} times` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc (mock HTTP only at LLM adapter boundary)
- do-write-concise-methods.mdc
- do-informative-logging.mdc
