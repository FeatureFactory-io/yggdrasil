# ACT-1-LLM-ANTHROPIC — Ratatosk Anthropic provider + unified BASE_MODEL config

**Tier:** 1
**Wave:** W3 (extends W1 config + W3 Ollama LLM)
**Feature files:**
- [`docs/features/act-1-ratatosk/ratatosk-config.feature`](../../../features/act-1-ratatosk/ratatosk-config.feature) — CFG-10..12
- [`docs/features/act-1-ratatosk/ratatosk-discovery.feature`](../../../features/act-1-ratatosk/ratatosk-discovery.feature) — LLM-05..06
**Package:** `02-ollama-llm/` (LLM port slice; not Ollama-specific despite folder name)
**Depends on:** ACT-1-CFG-06..09, ACT-1-LLM-01 (OllamaClient done), slice-1 `yggdrasil.llm.structured`
**Blocks:** Fast E2E certification (`test_e2e_real_bootstrap_mcp_query` with anthropic), cloud/desktop hybrid workflows

**Dr. Dobbs posture:** Prove each layer before stacking the next. No “wire Anthropic and hope bootstrap works.” Config resolution and adapter parsing are unit-testable without network; subprocess bootstrap is manual `@anthropic` only.

---

## Problem statement

Ratatosk discovery calls `llm.complete()` and parses JSON via [`yggdrasil.llm.structured`](../../../../src/yggdrasil/llm/structured.py). Ollama (thinking Qwen3) is too slow for routine E2E (~15–25 min). SAO already specifies `LLM_PROVIDER` swap and `AnthropicClient`, but:

- [`AnthropicClient.complete()`](../../../../src/yggdrasil/llm/adapters/anthropic.py) is `NotImplementedError`
- [`ratatosk/config.py`](../../../../ratatosk/config.py) `build_llm_from_config` has no `anthropic` branch
- No unified `BASE_MODEL`; split env vars only
- Repo/home YAML merge documented in features but not implemented for LLM keys

---

## Config contract (locked)

| Key | Source | Default (CLI) |
|-----|--------|---------------|
| `llm_provider` | flags → env → repo YAML → home YAML | `ollama` |
| `base_model` | same merge order | provider default alias (see below) |
| `anthropic_api_key` | **env only** (`ANTHROPIC_API_KEY`) | empty → fail if provider=anthropic |
| `ollama_base_url` | merge | `http://localhost:11434` |

**Backward compat:** `LLM_OLLAMA_MODEL` / `LLM_ANTHROPIC_MODEL` override `base_model` when set (document in `.env.example`).

**Alias registry** (`ratatosk/config.py` — pure function, unit-tested):

| `base_model` input | Provider | Resolved model id |
|--------------------|----------|-------------------|
| *(unset)* | anthropic | `claude-3-5-haiku-20241022` |
| `haiku` | anthropic | `claude-3-5-haiku-20241022` |
| `sonnet5` | anthropic | confirm at impl; log resolved id |
| *(unset)* | ollama | `qwen3:14b` |
| `qwen3:14b` | ollama | passthrough |

**Tests / CI:** `LLM_PROVIDER=scripted` remains explicit in [`test_settings.py`](../../../../src/yggdrasil/test_settings.py) and unit tests — never rely on empty env for scripted.

---

## Scenarios to add (Gherkin)

### Config feature — append to [`ratatosk-config.feature`](../../../features/act-1-ratatosk/ratatosk-config.feature)

```gherkin
  Scenario: ACT-1-CFG-10 LLM_PROVIDER anthropic selects Anthropic not Ollama
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "llm_provider" is "anthropic"

  Scenario: ACT-1-CFG-11 BASE_MODEL haiku resolves to Anthropic Haiku model id
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "BASE_MODEL" is set to "haiku"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap
    Then the effective config key "resolved_model" contains "haiku"

  Scenario: ACT-1-CFG-12 Repo .ratatosk/config.yaml sets llm_provider for bootstrap
    Given a repo config file ".ratatosk/config.yaml" with llm_provider "ollama"
    And a repo config file ".ratatosk/config.yaml" with base_model "qwen3:14b"
    When Ratatosk loads configuration for bootstrap with repo "./tests/fixtures/repos/sample_webapp"
    Then the effective config key "llm_provider" is "ollama"
    And the effective config key "resolved_model" is "qwen3:14b"

  Scenario: ACT-1-CFG-13 Environment overrides repo config for llm_provider
    Given a repo config file ".ratatosk/config.yaml" with llm_provider "ollama"
    And the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set to "sk-test-key"
    When Ratatosk loads configuration for bootstrap with repo "./tests/fixtures/repos/sample_webapp"
    Then the effective config key "llm_provider" is "anthropic"
```

**Amend ACT-1-CFG-08** (same file): when `LLM_PROVIDER` unset, effective `llm_provider` is `ollama` (not scripted). Add scenario or update existing step doc.

### Discovery feature — append to [`ratatosk-discovery.feature`](../../../features/act-1-ratatosk/ratatosk-discovery.feature)

```gherkin
  # ── ACT-1-LLM — Anthropic bootstrap (@anthropic optional manual cert) ─────

  @wip @anthropic
  Scenario: ACT-1-LLM-05 Bootstrap uses Anthropic when LLM_PROVIDER is anthropic
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is set
    And Priya has a Yggdrasil personal access token with read-write scope
    And the Yggdrasil model "Yggdrasil" exists with no elements
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the discovery LLM was invoked at least once
    And the output does not contain "scripted-discovery"
    And the output does not contain "Ollama request failed"

  @wip @anthropic
  Scenario: ACT-1-LLM-06 Bootstrap fails clearly when Anthropic API key is missing
    Given the environment variable "LLM_PROVIDER" is set to "anthropic"
    And the environment variable "ANTHROPIC_API_KEY" is not set
    And the fixture repository "sample_webapp" is available
    When Priya runs ratatosk bootstrap against fixture "sample_webapp" via subprocess
    Then the exit code is not 0
    And the output contains "ANTHROPIC_API_KEY"
```

### Catalog deltas (TFK-07 — implement with scenarios)

Add to [`docs/features/CATALOG.md`](../../../features/CATALOG.md):

| Step | Used by |
|------|---------|
| `Given a repo config file "{path}" with llm_provider "{value}"` | CFG-12, CFG-13 |
| `Given a repo config file "{path}" with base_model "{value}"` | CFG-12 |
| `When Ratatosk loads configuration for bootstrap with repo "{path}"` | CFG-12, CFG-13 |
| `Then the effective config key "resolved_model" is "{value}"` | CFG-11, CFG-12 |
| `Then the effective config key "resolved_model" contains "{substring}"` | CFG-11 |
| `Given the environment variable "ANTHROPIC_API_KEY" is set` | LLM-05 (uses real env in manual run) |
| `Given the environment variable "ANTHROPIC_API_KEY" is not set` | LLM-06 |

Fixture: [`tests/fixtures/repos/sample_webapp/.ratatosk/config.yaml`](../../../../tests/fixtures/repos/sample_webapp/.ratatosk/config.yaml) — repo config stub for CFG-12/13.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| [`ratatosk/config.py`](../../../../ratatosk/config.py) | 33–120 | Extend loader + `build_llm_from_config`; **no Django** |
| [`src/yggdrasil/llm/adapters/ollama.py`](../../../../src/yggdrasil/llm/adapters/ollama.py) | 61–180 | Mirror pattern: `_build_payload`, `_parse_response`, thinking isolation, 8000 tokens, 300s timeout |
| [`src/yggdrasil/llm/adapters/anthropic.py`](../../../../src/yggdrasil/llm/adapters/anthropic.py) | 42–73 | **Implement** — today all `NotImplementedError` |
| [`src/yggdrasil/llm/structured.py`](../../../../src/yggdrasil/llm/structured.py) | all | Reuse for JSON extract — do NOT duplicate parsers in runner/agent |
| [`src/yggdrasil/llm/base.py`](../../../../src/yggdrasil/llm/base.py) | 32–45 | `LLMResponse.thinking` field already exists |
| [`src/yggdrasil/ratatosk/llm_factory.py`](../../../../src/yggdrasil/ratatosk/llm_factory.py) | 137–173 | Django in-process path — align with `build_llm_from_config` |
| [`ratatosk/cli.py`](../../../../ratatosk/cli.py) | 118–136 | Pass `repo_path=path` into `load_bootstrap_config` |
| [`ratatosk/tests/test_config_loader.py`](../../../../ratatosk/tests/test_config_loader.py) | all | Extend CFG tests; fix default-provider test |
| [`docs/features/steps/cli_steps.py`](../../../features/steps/cli_steps.py) | CFG stubs | Wire new catalog steps for CFG-10..13 |

**MCP / Agent surface:** Not applicable — Ratatosk CLI calls LLM directly; no new MCP tools.

---

## Do Not Do

Inherit [`SHARED-CONTRACT.md`](../00-foundation/SHARED-CONTRACT.md), plus:

- Do NOT import Django in `ratatosk/config.py`.
- Do NOT store `ANTHROPIC_API_KEY` in repo or home YAML (CFG-04 pattern — env only).
- Do NOT silently fall back to `ScriptedDiscoveryLLM` when `LLM_PROVIDER=anthropic` or `ollama` — fail fast with clear error.
- Do NOT enable Anthropic extended thinking for Ratatosk field tier in this slice (JSON latency); parse thinking blocks if model returns them, but do not request thinking budget.
- Do NOT add Anthropic to default CI (`make test`) — manual `@anthropic` / optional job only.
- Do NOT log API keys, raw prompts, or full LLM responses at INFO.
- Do NOT modify root `pyproject.toml` — `anthropic>=0.32` already present.
- Do NOT implement full scout bounds YAML merge (CFG-01) — LLM keys only in this slice.
- Do NOT reintroduce Payment API hardcoded candidates outside `LLM_PROVIDER=scripted`.

---

## SAO.md Sections That Apply

- **§2 LLM abstraction** — `LLMClient` protocol; `LLM_PROVIDER` env; thinking models normalized at adapter boundary
- **§17.3 Ratatosk Field/Batch** — small/fast LLM for map/extract; element ops only
- **§17.6 Model tiers** — Haiku default for Anthropic field tier; Sonnet via explicit `BASE_MODEL=sonnet5`
- **§18 external integrations** — CLI uses env + YAML merge, not in-process Django settings for bootstrap subprocess
- **CLI config merge** (§17.3 / user journey) — flags → env → repo `.ratatosk/config.yaml` or `ratatosk.yaml` → `~/.ratatosk/config.yaml`

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_anthropic_complete_posts_to_messages_api` | unit | Mock SDK: POST shape, system + messages, max_tokens |
| `test_anthropic_parse_response_isolates_thinking_blocks` | unit | Text → `content`; thinking → `LLMResponse.thinking` |
| `test_anthropic_complete_missing_key_raises_llm_error` | unit | No key → `LLMError` before network |
| `test_resolve_base_model_haiku_for_anthropic` | unit | `BASE_MODEL=haiku` → haiku API id |
| `test_resolve_base_model_sonnet5_alias` | unit | Alias maps to concrete id; unknown alias → clear error |
| `test_resolve_base_model_qwen_passthrough` | unit | Ollama tag unchanged |
| `test_load_config_llm_provider_anthropic_from_env` | unit | CFG-10 |
| `test_load_config_default_provider_is_ollama_not_scripted` | unit | CFG-08 amendment; empty env → ollama |
| `test_load_config_repo_yaml_sets_llm_provider` | unit | CFG-12 with temp dir fixture |
| `test_load_config_env_overrides_repo_yaml` | unit | CFG-13 |
| `test_build_llm_returns_anthropic_client_when_configured` | unit | isinstance `AnthropicClient`, not Ollama |
| `test_build_llm_anthropic_missing_key_raises` | unit | CFG-10/LLM-06 fail-fast |
| `test_build_llm_scripted_only_when_explicit` | unit | `LLM_PROVIDER=scripted` → ScriptedDiscoveryLLM |
| `test_journey_bootstrap_then_update_via_mcp` | integration | Regression: scripted path unchanged |
| `test_cfg10_behave_effective_config_key` | behave | CFG-10 Gherkin (when TFK-07 wired) |
| `test_llm06_behave_missing_api_key` | behave | LLM-06 Gherkin (when TFK-07 wired) |

**Manual (not CI default):**

| Test | Level | Proves |
|------|-------|--------|
| `test_e2e_real_bootstrap_mcp_query` with `LLM_PROVIDER=anthropic` | e2e | Full subprocess + MCP query; manifest elements in graph |

Rules: [`do-test-first.mdc`](../../../../.cursor/rules/do-test-first.mdc) · [`pytest.mdc`](../../../../.cursor/rules/pytest.mdc) · mock SDK only in unit tests, not integration.

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `load_bootstrap_config` entry | config load | repo_path, merge sources present |
| `load_bootstrap_config` exit | resolved config | llm_provider, base_model (raw), resolved_model, ollama_base_url; **never** api_key |
| `_load_yaml_layers` | each file read | path, keys loaded (llm_provider, base_model only) |
| `_resolve_base_model` | alias branch | provider, input, resolved_id, branch=alias\|passthrough\|default |
| `build_llm_from_config` | provider branch | provider, client class name, resolved_model |
| `build_llm_from_config` reject | anthropic no key | reason=missing_api_key |
| `AnthropicClient.complete` entry | LLM call | model, messages count, max_tokens |
| `AnthropicClient.complete` result | success | content_chars, thinking_chars, usage, stop_reason |
| `AnthropicClient.complete` error | SDK failure | model, error class; no key in message |

Logs go to `logs/ratatosk.log` (CLI) per existing ratatosk logging setup.

---

## MCP Tools to Expose

Not applicable.

---

## Implementation order (red → green → refactor)

Rules applied: [`do-test-first.mdc`](../../../../.cursor/rules/do-test-first.mdc) · [`do-small-increments.mdc`](../../../../.cursor/rules/do-small-increments.mdc) · [`do-informative-logging.mdc`](../../../../.cursor/rules/do-informative-logging.mdc) (final slice only).

**Workflow per slice:** write failing test → run pytest (confirm red) → minimum code to pass → run pytest (green) → refactor → run pytest again. **Do not start slice N+1 until slice N checkpoint is green.**

**Prerequisite (slice 0):** Create a feature branch and commit all **existing uncommitted W0–W8 work** wave-by-wave per [`INDEX.md`](../INDEX.md) **before** slice 1. Anthropic slices 1–11 build on a clean, wave-organized baseline — not a mixed dirty working tree.

**Spec-first (slice 1):** Gherkin scenarios and catalog steps are written **before** any new Anthropic runtime code. Pytest tests in slices 2–10 map to scenario IDs (CFG-10..13, LLM-05..06). Implementation proves the spec, not the other way around.

---

### Slice 0 — Branch + wave-by-wave baseline commits (prerequisite)

Organize the current dirty working tree into one branch with **one commit per wave**, each gated by the wave checkpoint from [`INDEX.md`](../INDEX.md). Do not start slice 1 until slice 0 is complete.

#### Red
1. Confirm on `main` (or agreed base) with uncommitted changes: `git status --short`.
2. Identify stray/accidental files (e.g. `tail`) — delete or exclude from commits.

#### Green — branch
3. Create branch from current base:
   ```bash
   git checkout -b feature/bootstrap-mvp-w0-w8-baseline
   ```

#### Green — one commit per wave (run gate → stage wave files → commit)

| Order | Wave | Package | Files (current working tree) | Gate before commit |
|-------|------|---------|------------------------------|-------------------|
| 1 | W0 | `00-foundation` | `tests/integration/test_journey_bootstrap_then_update.py` | `uv run pytest tests/integration/test_journey_bootstrap_then_update.py -x` |
| 2 | W1 | `01-config` | `ratatosk/config.py`, `ratatosk/tests/test_config_loader.py`, `docs/features/steps/cli_steps.py` (CFG steps only) | `uv run pytest ratatosk/tests/test_config_loader.py -x` |
| 3 | W2 | `05-mcp-handoff` | `src/yggdrasil/mcp/server.py`, `src/yggdrasil/mcp/http_bridge.py`, `src/yggdrasil/mcp/tools/propose.py`, `src/yggdrasil/mcp/tools/changeset.py`, `ratatosk/mcp_client.py`, `tests/integration/mcp_harness/` | `uv run pytest src/yggdrasil/mcp/tests/test_propose_changeset.py tests/integration/mcp_harness/ -x` |
| 4 | W3 | `02-ollama-llm` | `src/yggdrasil/llm/structured.py`, `src/yggdrasil/llm/base.py`, `src/yggdrasil/llm/adapters/ollama.py`, `src/yggdrasil/llm/tests/`, `docs/architecture/SAO.md` (thinking-model section) | `uv run pytest src/yggdrasil/llm/tests/test_ollama_client.py src/yggdrasil/llm/tests/test_structured.py -x` |
| 5 | W4 | `04-discovery` | `ratatosk/discovery/runner.py`, `ratatosk/discovery/model_summary.py`, `ratatosk/discovery/scripted_llm.py`, `src/yggdrasil/ratatosk/agent.py`, `src/yggdrasil/ratatosk/model_summary.py`, `src/yggdrasil/ratatosk/llm_factory.py`, `src/yggdrasil/ratatosk/tests/test_discovery_agent.py`, `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | `uv run pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py -x` |
| 6 | W5 | `03-cli-bootstrap` | `ratatosk/cli.py`, `ratatosk/tests/test_cli_click.py` | `uv run pytest ratatosk/tests/test_cli_click.py -x` |
| 7 | W6 | `06-munin-linking` | `src/yggdrasil/munin/bootstrap_planner.py`, `src/yggdrasil/munin/tests/test_bootstrap_handoff.py`, `src/yggdrasil/changeset/services.py` | `uv run pytest src/yggdrasil/munin/tests/test_bootstrap_handoff.py -x` |
| 8 | W7 | `07-mcp-query` | `src/yggdrasil/mcp/tools/query.py`, `src/yggdrasil/mcp/tests/test_query_tools.py`, `src/yggdrasil/urls.py` | `uv run pytest src/yggdrasil/mcp/tests/test_query_tools.py -x` |
| 9 | W8 | `08-mcp-changeset` | `src/yggdrasil/mcp/tests/test_approve_changeset.py` | `uv run pytest src/yggdrasil/mcp/tests/test_approve_changeset.py -x` |
| 10 | — | cross-cutting | `pyproject.toml`, `docs/plans/bootstrap-mvp/` (except `ACT-1-LLM-ANTHROPIC-PROVIDER.md` — reserved for slice 1), E2E stub `tests/integration/test_e2e_real_bootstrap_mcp_query.py` | `uv run pytest tests/integration/ -x --ignore=tests/integration/test_e2e_real_bootstrap_mcp_query.py` |

4. Commit message pattern per wave (Angular convention):
   ```
   feat(bootstrap-mvp): W{N} {package} — {one-line summary}

   Wave checkpoint green: {pytest command from INDEX}
   ```

#### Refactor
5. `git status --short` must be empty (or only `ACT-1-LLM-ANTHROPIC-PROVIDER.md` if deferring plan doc to slice 1).
6. Optional: squash-fix any gate failure on the same wave before moving to next wave — never commit W{N+1} while W{N} gate is red.

**Checkpoint:** Branch `feature/bootstrap-mvp-w0-w8-baseline` with W0..W8 commits; working tree clean; all wave gates green.

---

### Slice 1 — Gherkin, catalog, contract docs (spec-first — guides slices 2–10)

Per [`do-test-first.mdc`](../../../../.cursor/rules/do-test-first.mdc): BDD scenarios in `docs/features/` define acceptance criteria; tag unimplemented paths `@wip`.

#### Red
1. Grep feature files — confirm CFG-10..13 and LLM-05..06 **do not yet exist**.
2. Grep [`CATALOG.md`](../../../features/CATALOG.md) — confirm repo-config and `resolved_model` steps missing.
3. Note: no pytest checkpoint yet — spec artifacts are the deliverable.

#### Green
4. Append CFG-10..13 to [`ratatosk-config.feature`](../../../features/act-1-ratatosk/ratatosk-config.feature) (see **Scenarios to add** above).
5. Amend ACT-1-CFG-08: unset `LLM_PROVIDER` → effective `ollama` (not scripted).
6. Append LLM-05..06 to [`ratatosk-discovery.feature`](../../../features/act-1-ratatosk/ratatosk-discovery.feature) with `@wip @anthropic`.
7. Add catalog rows to [`CATALOG.md`](../../../features/CATALOG.md) (TFK-07 table above).
8. Stub steps in [`cli_steps.py`](../../../features/steps/cli_steps.py) — call `load_bootstrap_config`; raise `NotImplementedError` or `@wip` skip until slice 8 wires YAML.
9. Update [`.env.example`](../../../../.env.example) — `LLM_PROVIDER`, `BASE_MODEL`, alias table, `ANTHROPIC_API_KEY` env-only note, legacy `LLM_*_MODEL` overrides.
10. Update [`SAO.md`](../../../architecture/SAO.md) — Anthropic adapter, merge order, Haiku default.
11. Update [`INDEX.md`](../INDEX.md) — ACT-1-LLM-ANTHROPIC row with scenario IDs.

#### Refactor
12. Cross-check scenario IDs, step phrases, and **Tests to Create** table — every pytest test name should trace to a CFG/LLM scenario ID.
13. Run `uv run behave docs/features/act-1-ratatosk/ratatosk-config.feature --tags=@wip` — expect skips/failures on new steps (acceptable; proves spec is ahead of code).

**Checkpoint:** Feature files + catalog + docs committed; scenario IDs stable. **No runtime implementation in this slice.**

---

### Slice 2 — `AnthropicClient._parse_response` (pure, no network)

#### Red
1. Create [`src/yggdrasil/llm/tests/test_anthropic_client.py`](../../../../src/yggdrasil/llm/tests/test_anthropic_client.py).
2. Add `test_anthropic_parse_response_text_only` — mock API dict with text block → `content` populated, `thinking=""`.
3. Add `test_anthropic_parse_response_isolates_thinking_blocks` — dict with thinking + text blocks → separate fields.
4. Run: `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -k parse -x` → **must fail** (`NotImplementedError`).

#### Green
5. Implement `_parse_response(raw: dict) -> LLMResponse` only in [`anthropic.py`](../../../../src/yggdrasil/llm/adapters/anthropic.py) — extract text/thinking from content blocks; usage from response metadata.
6. Run same pytest → **green**.

#### Refactor
7. Extract `_extract_text_blocks(message) -> tuple[str, str]` helper if `_parse_response` exceeds ~25 lines.
8. Re-run pytest.

**Checkpoint:** `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -k parse -x`

---

### Slice 3 — `AnthropicClient._build_payload` + `__init__`

#### Red
1. Add `test_anthropic_init_missing_key_raises_llm_error` — empty api_key → `LLMError` before SDK call.
2. Add `test_anthropic_build_payload_includes_system_and_messages` — assert payload shape (system separate, user message present, max_tokens=8000).
3. Run: `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -k "init or payload" -x` → **red**.

#### Green
4. Implement `__init__` — require api_key from arg or `ANTHROPIC_API_KEY` env; set `model_id`.
5. Implement `_build_payload(messages, system, max_tokens, temperature) -> dict`.
6. Run pytest → **green**.

#### Refactor
7. Add module constants `_DEFAULT_MAX_TOKENS = 8000`, `_DEFAULT_MODEL` (Haiku id).
8. Re-run pytest.

**Checkpoint:** `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -k "init or payload" -x`

---

### Slice 4 — `AnthropicClient.complete` (mocked SDK)

#### Red
1. Add `test_anthropic_complete_posts_to_messages_api` — mock `anthropic.Anthropic.messages.create`; assert called once; returns parsed `LLMResponse`.
2. Add `test_anthropic_complete_sdk_error_raises_llm_error` — mock raises `APIError` → `LLMError` with model in message.
3. Run: `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -k complete -x` → **red**.

#### Green
4. Implement `complete()` — build payload, call SDK, `_parse_response`, return `LLMResponse`.
5. Map SDK exceptions → `LLMError` (no raw key in error text).
6. Run pytest → **green**.

#### Refactor
7. Ensure `complete()` ≤ 30 lines; delegate to `_call_sdk(payload)`.
8. Re-run full `test_anthropic_client.py`.

**Checkpoint:** `uv run pytest src/yggdrasil/llm/tests/test_anthropic_client.py -x`

---

### Slice 5 — `_resolve_base_model` pure function (CFG-11)

#### Red
1. Add `test_resolve_base_model_haiku_for_anthropic` — provider=anthropic, input=haiku → id contains `haiku`.
2. Add `test_resolve_base_model_sonnet5_alias` — sonnet5 → concrete API id (assert prefix/suffix, not magic string in test doc).
3. Add `test_resolve_base_model_qwen_passthrough` — ollama + qwen3:14b unchanged.
4. Add `test_resolve_base_model_unknown_alias_raises` — bogus alias → `ValueError` with alias name.
5. Add `test_resolve_base_model_legacy_env_override` — `LLM_ANTHROPIC_MODEL` wins over `BASE_MODEL` when set.
6. Run: `uv run pytest ratatosk/tests/test_config_loader.py -k resolve -x` → **red** (function missing).

#### Green
7. Add `_MODEL_ALIASES` and `_resolve_base_model(provider, raw, env) -> str` to [`ratatosk/config.py`](../../../../ratatosk/config.py).
8. Add `resolved_model: str` field to `BootstrapConfig`; populate in loader.
9. Run pytest → **green**.

#### Refactor
10. Keep `_resolve_base_model` pure (no I/O); single responsibility.
11. Re-run pytest.

**Checkpoint:** `uv run pytest ratatosk/tests/test_config_loader.py -k resolve -x`

---

### Slice 6 — `build_llm_from_config` anthropic branch (CFG-10, LLM-06)

#### Red
1. Add `test_load_config_llm_provider_anthropic_from_env` — CFG-10.
2. Add `test_build_llm_returns_anthropic_client_when_configured` — isinstance check, not Ollama/Scripted.
3. Add `test_build_llm_anthropic_missing_key_raises` — message contains `ANTHROPIC_API_KEY`.
4. Run: `uv run pytest ratatosk/tests/test_config_loader.py -k anthropic -x` → **red**.

#### Green
5. Add `anthropic` branch in `build_llm_from_config` → `AnthropicClient(model=config.resolved_model, api_key=...)`.
6. Fail fast when provider=anthropic and key empty.
7. Run pytest → **green**.

#### Refactor
8. Remove duplicate anthropic wiring from [`llm_factory.py`](../../../../src/yggdrasil/ratatosk/llm_factory.py) — call `build_llm_from_config` or shared helper (single source).
9. Re-run `ratatosk/tests/test_config_loader.py` + `test_discovery_agent.py`.

**Checkpoint:** `uv run pytest ratatosk/tests/test_config_loader.py -k anthropic -x`

---

### Slice 7 — Default provider `ollama` (CFG-08 amendment)

#### Red
1. Rename/replace `test_build_llm_returns_scripted_by_default`:
   - `test_load_config_default_provider_is_ollama_not_scripted` — empty env → `llm_provider==ollama`.
   - `test_build_llm_scripted_only_when_explicit` — `LLM_PROVIDER=scripted` → ScriptedDiscoveryLLM.
2. Run: `uv run pytest ratatosk/tests/test_config_loader.py -k "default or scripted" -x` → **red**.

#### Green
3. Change `load_bootstrap_config` default: `llm_provider="ollama"` when env key absent.
4. Keep `build_llm_from_config`: scripted only when `provider=="scripted"` (remove empty/auto → scripted).
5. Fix any broken tests that assumed empty env → scripted (grep `load_bootstrap_config(env={})`).
6. Run pytest → **green**.

#### Refactor
7. Document default in docstring on `load_bootstrap_config`.
8. Re-run `uv run pytest ratatosk/tests/ -x`.

**Checkpoint:** `uv run pytest ratatosk/tests/test_config_loader.py -x`

---

### Slice 8 — YAML merge for LLM keys (CFG-12, CFG-13)

#### Red
1. Add fixture helper in test file: write temp `{repo}/.ratatosk/config.yaml`.
2. Add `test_load_config_repo_yaml_sets_llm_provider_and_model` — CFG-12.
3. Add `test_load_config_env_overrides_repo_yaml` — repo says ollama, env says anthropic → anthropic wins.
4. Add `test_load_config_yaml_ignores_api_key_field` — YAML with `anthropic_api_key` key ignored/warned (optional).
5. Run: `uv run pytest ratatosk/tests/test_config_loader.py -k yaml -x` → **red**.

#### Green
6. Implement `_load_yaml_file(path) -> dict` and `_load_yaml_layers(repo_path) -> dict` (home → repo merge).
7. Wire merge into `load_bootstrap_config(repo_path=...)` — env applied last.
8. Update [`ratatosk/cli.py`](../../../../ratatosk/cli.py): pass `repo_path=path` on bootstrap and update.
9. Add [`tests/fixtures/repos/sample_webapp/.ratatosk/config.yaml`](../../../../tests/fixtures/repos/sample_webapp/.ratatosk/config.yaml) stub.
10. Run pytest → **green**.

#### Refactor
11. Restrict merged YAML keys to allowlist: `llm_provider`, `base_model`, `ollama_base_url`, `model_summary_token_budget`.
12. Re-run pytest.

**Checkpoint:** `uv run pytest ratatosk/tests/test_config_loader.py -k yaml -x`

---

### Slice 9 — Integration regression sweep

#### Red
1. Run full unit + integration suite: `uv run pytest ratatosk/tests/ src/yggdrasil/llm/tests/ src/yggdrasil/ratatosk/tests/test_discovery_agent.py tests/integration/test_journey_bootstrap_then_update.py -x`.

#### Green
2. Fix any failures from default-provider or factory refactor.

**Checkpoint:** same command — all green.

---

### Slice 10 — Manual E2E certification (LLM-05, not CI)

#### Red
1. Run (requires real key):
   ```bash
   YGGDRASIL_E2E=1 LLM_PROVIDER=anthropic BASE_MODEL=haiku \
     uv run pytest tests/integration/test_e2e_real_bootstrap_mcp_query.py -m e2e_real -s \
     > /tmp/e2e_anthropic.log 2>&1
   cat /tmp/e2e_anthropic.log | tail -40
   ```

#### Green
2. If fail: diagnose via `logs/ratatosk.log` + `/tmp/e2e_anthropic.log`; fix only blocking defect (out of scope items filed separately).

**Acceptance:** manifest names in graph; bootstrap completes faster than Ollama path.

---

### Slice 11 — Informative logging pass (final, all new/changed methods)

Apply [`do-informative-logging.mdc`](../../../../.cursor/rules/do-informative-logging.mdc) to **every public and decision-point method** touched in slices 2–10. Logging is intentionally deferred to this slice so red/green tests stay focused on behavior.

#### Red
1. Read **Logs to Emit** table (below); for each row, grep `logs/ratatosk.log` after a local bootstrap/config load — mark missing lines.

#### Green — per file

**[`anthropic.py`](../../../../src/yggdrasil/llm/adapters/anthropic.py)**
2. `__init__` exit: INFO `model_id` (never key).
3. `complete` entry: model, message count, max_tokens.
4. `complete` success exit: content_chars, thinking_chars, usage, stop_reason.
5. `complete` error: model, exception class; no key, no prompt body at INFO.
6. `_parse_response` decision: log when thinking blocks stripped (DEBUG ok).

**[`ratatosk/config.py`](../../../../ratatosk/config.py)**
7. `load_bootstrap_config` entry: repo_path, sources=flags+env+yaml.
8. `load_bootstrap_config` exit: llm_provider, base_model, resolved_model, ollama_base_url.
9. `_load_yaml_layers`: each file path loaded + keys merged (INFO).
10. `_resolve_base_model`: provider, input, resolved_id, branch=alias|default|legacy_env|passthrough.
11. `build_llm_from_config` entry: provider; exit: client class + resolved_model.
12. `build_llm_from_config` reject anthropic no key: reason=missing_api_key.

**[`ratatosk/cli.py`](../../../../ratatosk/cli.py)** (if touched)
13. bootstrap/update: log effective provider + resolved_model after config load.

#### Refactor
14. Remove duplicate/noisy logs; ensure no secrets at INFO.
15. Manual verify: run `ratatosk bootstrap` once with ollama + once with anthropic (if key available); read `logs/ratatosk.log` against **Logs to Emit** checklist.

**Checkpoint:** All **Logs to Emit** rows ticked; no new test failures: `uv run pytest ratatosk/tests/ src/yggdrasil/llm/tests/ -x`

---

## Logs to Emit

- [ ] All rows in **Tests to Create** (unit + integration) pass via pytest
- [ ] `LLM_PROVIDER=anthropic` + valid key → `AnthropicClient` used; no silent fallback
- [ ] `LLM_PROVIDER=anthropic` + missing key → non-zero exit, message mentions `ANTHROPIC_API_KEY`
- [ ] `LLM_PROVIDER` unset → `ollama` + `qwen3:14b` (CLI)
- [ ] `BASE_MODEL=haiku` → Haiku model id in logs as `resolved_model`
- [ ] Repo `.ratatosk/config.yaml` merges; env overrides repo for `llm_provider`
- [ ] **Slice 0:** branch created; W0–W8 baseline commits green; working tree clean
- [ ] Slice 1 spec (Gherkin + catalog + docs) committed before runtime slices
- [ ] Slices 2–10 complete with red → green → refactor checkpoints green
- [ ] **Slice 11 (logging):** each **Logs to Emit** row verified in `logs/ratatosk.log` on happy + reject paths
- [ ] No regression: `pytest tests/integration/test_journey_bootstrap_then_update.py -x`
- [ ] Gherkin scenarios added to feature files; catalog steps documented (TFK-07)
- [ ] Manual E2E with anthropic documented (optional sign-off)

---

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Default provider `ollama` breaks tests expecting scripted | Explicit `LLM_PROVIDER=scripted` in test_settings and unit tests |
| `sonnet5` alias wrong API id | Log resolved id at startup; confirm against Anthropic docs at impl |
| API cost on manual E2E | `@anthropic` marker; document token usage; prefer Haiku |
| Config drift CLI vs Django agent | Single resolver in `ratatosk.config`; llm_factory imports it |
| YAML merge scope creep | LLM keys only; defer scout bounds to CFG-01 |

---

## Out of scope (explicit deferrals)

- OpenAI adapter
- Munin extended-thinking request budget
- Package-slug cleanup in discovery `_cleanup`
- Project-map directory-vs-file target fix
- `ratatosk doctor` (CFG-05)
- GitHub issues (PIN playbook)

---

## Commit strategy (small increments)

**Slice 0 (baseline, one-time):** up to 10 wave commits on `feature/bootstrap-mvp-w0-w8-baseline` — see slice 0 table above.

**Slices 1–11 (Anthropic feature):** one commit per slice checkpoint (11 commits):

0. *(slice 0 — wave baseline commits, not counted in Anthropic slice total)*
1. `docs(features): add CFG-10..13 LLM-05..06 scenarios, catalog, SAO, .env.example` **(spec-first)**
2. `test(llm): red tests for AnthropicClient parse`
3. `feat(llm): implement AnthropicClient parse + payload + complete (green)`
4. `test(ratatosk): red tests for BASE_MODEL resolution (CFG-11)`
5. `feat(ratatosk): resolve BASE_MODEL aliases (green)`
6. `test(ratatosk): red tests for anthropic provider branch (CFG-10, LLM-06)`
7. `feat(ratatosk): wire anthropic in build_llm_from_config`
8. `fix(ratatosk): default LLM_PROVIDER to ollama; scripted explicit only (CFG-08)`
9. `test(ratatosk): red tests for YAML llm config merge (CFG-12, CFG-13)`
10. `feat(ratatosk): merge llm keys from repo/home YAML`
11. `chore(ratatosk): informative logging pass on anthropic config paths`

Each commit: run that slice's checkpoint pytest before committing. Slice 10 (manual E2E) is sign-off only — no commit unless a fix is required.
