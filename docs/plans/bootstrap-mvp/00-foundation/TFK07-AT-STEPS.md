# TFK07-AT-STEPS — Behave step batch for bootstrap MVP

**Type:** Foundation work item (not a Gherkin scenario ID)
**Tier:** W0 prerequisite
**Wave:** W0
**Depends on:** [SHARED-CONTRACT.md](SHARED-CONTRACT.md)
**Blocks:** DISC-21, LLM-01..04, CFG-06..09, CLI-01, MCP query AT scenarios

---

## Problem statement

Many bootstrap MVP scenarios are `@wip` because step definitions in `docs/features/steps/` raise `NotImplementedError`. Gherkin phrases exist in [docs/features/CATALOG.md](../../features/CATALOG.md) but AT cannot run until TFK-07 implements them.

This plan covers the **minimum step batch** to unblock W1–W7 scenario AT runs — not every Act 5 MCP phrase.

---

## Scenario coverage (what these steps unblock)

| Step phrase | Scenarios |
|-------------|-----------|
| `Given the environment variable "{name}" is set to "{value}"` | CFG-09, CLI-09, DISC-21, LLM-* |
| `When Ratatosk loads configuration for bootstrap` | CFG-06..09 |
| `Then the effective config key "{key}" is {value}` | CFG-06..09, CFG-02 |
| `When Priya runs ratatosk bootstrap against fixture "{name}" via subprocess` | DISC-21, LLM-01..03 |
| `Then MCP tool "{tool}" was called during bootstrap` | DISC-21 |
| `Given Ollama is reachable at "{url}"` | LLM-01, LLM-03 |
| `Given Ollama model "{model}" is not available` | LLM-02 |
| `Then bootstrap candidates include all manifest elements:` | DISC-01, LLM-03 |
| `And the output contains wipe no-op for empty graph` | CLI-08 |

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `docs/features/steps/cli_steps.py` | 557+ | `@wip` stubs for env, subprocess, config loader |
| `docs/features/steps/discovery_steps.py` | 1–494 | Manifest table assert, fixture bootstrap |
| `docs/features/steps/mcp_steps.py` | 1–50 | Honest contract: T2 direct callables today; T1 optional later |
| `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | all | Manifest source for candidate asserts |
| `ratatosk/tests/test_cli_click.py` | all | Pytest patterns for subprocess/MCP spy to mirror in behave |

---

## Do Not Do

Inherit [SHARED-CONTRACT.md](SHARED-CONTRACT.md), plus:

- Do NOT implement subprocess steps by shelling out to cloud default server — respect `YGGDRASIL_SERVER_URL` or use mocked HTTP for CI without server.
- Do NOT make behave steps import `django.setup()` in the ratatosk package path used by subprocess tests.
- Do NOT duplicate manifest parsing logic — read `expected_elements.yaml` once in a shared helper.

---

## Current State Assessment

### Exists

- In-process bootstrap steps in `discovery_steps.py` (fixture repo via `bootstrap_repository`).
- `cli_steps.py` with token/path steps for CLI-06 style errors.
- CATALOG documents intended phrases.

### Missing / stub

- `step_env_var_set` → `NotImplementedError`
- `step_load_config_for_bootstrap` → `NotImplementedError`
- Subprocess bootstrap with MCP call recording.
- Ollama reachability probes (can use `urllib` HEAD/GET to `/api/tags`).
- Wipe no-op phrase step mapping to `wiping 0 elements and 0 relationships`.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_env_var_step_sets_context` | behave unit | `context.env` receives var before CLI invoke |
| `test_config_loader_step_reads_merged_config` | behave + pytest | `llm_provider=ollama` when env set |
| `test_subprocess_bootstrap_records_mcp_tools` | integration | Spy on `RatatoskMcpClient.call_tool` names |
| `test_manifest_table_step_matches_changeset_ops` | integration | 4/4 names from `expected_elements.yaml` in propose payload |
| `test_ollama_unreachable_skips_ollama_scenarios` | marker | `@ollama` scenarios skip when no daemon |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `cli_steps.step_env_var_set` | env injected | var name (not secret value if token) |
| `cli_steps.step_subprocess_bootstrap` | before Popen | command argv sans token, fixture path |
| `cli_steps.step_subprocess_bootstrap` | after exit | exit_code, tools_called list |
| `discovery_steps.step_manifest_elements` | assert | expected vs actual candidate names, missing list |

---

## MCP Tools to Expose

Not applicable — this package implements test steps, not new MCP tools.

---

## Implementation Steps

1. **Red:** Add pytest for config merge helper in `ratatosk/config.py` (see CFG-06) callable from step `When Ratatosk loads configuration for bootstrap`.
2. **Green:** Implement `Given the environment variable` using `context.env_overrides` dict applied via `monkeypatch` or subprocess env copy.
3. **Green:** Implement manifest table step: load YAML, compare to ChangeSetItem names or blackboard extract list.
4. **Green:** Subprocess step: copy `sample_webapp` to temp dir, run `ratatosk bootstrap` with `YGGDRASIL_SERVER_URL` pointing at test server OR wrap client with recording proxy for unit-style behave.
5. **Green:** Ollama steps: probe `OLLAMA_BASE_URL/api/tags`; skip scenario if unreachable unless `@ollama` strict mode.
6. **Refactor:** Extract `_load_expected_manifest(fixture_name)` shared by DISC-01 and LLM-03 steps.

---

## Checkpoint

```bash
pytest docs/features/steps/ -x -k "config or manifest" 2>/dev/null || behave docs/features/act-1-ratatosk/ratatosk-config.feature --tags=-wip -n 1
```

Pragmatic gate: CFG-06..09 scenarios runnable in behave without `NotImplementedError` on config steps.

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-small-increments.mdc
- do-informative-logging.mdc
