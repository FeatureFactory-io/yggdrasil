# ACT-1-CFG-02 — CLI flag overrides repo config for model summary budget

> **DEFER (Tier 4)** — Implement after W0–W9 green. Plan is complete for PIN handoff.

**Tier:** 4 (optional early W1 if low cost)
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-config.feature`
**Package:** `01-config/`
**Depends on:** ACT-1-DISC-15 (ModelSummary in runner)
**Blocks:** ACT-1-MSUM-* scenarios

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CFG-02 CLI flag overrides repo config for model summary budget
  Given a repo config file "ratatosk.yaml" with model_summary_token_budget 8000
  When Priya runs ratatosk bootstrap with flag "--model-summary-budget 4000"
  Then the effective config key "model_summary_token_budget" is 4000
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/config.py` | merge | CLI flag highest precedence |
| `ratatosk/discovery/runner.py` | ModelSummary | Consumer of budget |
| `tests/fixtures/repos/sample_webapp/ratosk.yaml` | all | Repo config stub |

---

## Do Not Do

Inherit SHARED-CONTRACT. Do NOT implement merge without DISC-15 blackboard key — budget must affect runtime, not just config object.

---

## Current State Assessment

- Repo `ratatosk.yaml` exists in fixture but runner does not read budget from config yet.
- No `--model-summary-budget` Click option on bootstrap.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_config_flag_overrides_repo_model_summary_budget` | unit | 4000 wins over 8000 |
| `test_runner_respects_reduced_budget` | integration | blackboard chars lower with 4000 |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `load_bootstrap_config` | merge | model_summary_token_budget source=flag |
| runner ModelSummary step | build | budget, chars used |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Add Click option `--model-summary-budget` on bootstrap.
2. Extend config merge for int budget.
3. Pass budget into runner / agent ModelSummary builder.
4. Assert DISC-15 `model_summary_chars` respects lower cap.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_config_loader.py::test_config_flag_overrides_repo_model_summary_budget -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
