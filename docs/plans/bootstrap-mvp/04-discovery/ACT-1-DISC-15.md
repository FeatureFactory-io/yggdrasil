# ACT-1-DISC-15 — Run blackboard records ModelSummary token budget

**Tier:** 1
**Wave:** W4
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** ModelSummary builder in runner
**Blocks:** ACT-1-CFG-02 (deferred), scout ModelSummary (Act 6)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-15 Run blackboard records ModelSummary token budget
  ...
  Then the run blackboard contains key "model_summary_chars"
  And the run blackboard model_summary_chars is at most 8000 tokens equivalent
```

---

## Why this scenario matters

ModelSummary must respect **8000-token budget** (SAO A5) — stored on blackboard for briefing and debugging. Chars key is conservative proxy until tokenizer wired; cap prevents unbounded prompt growth.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | ModelSummary | Budget enforcement |
| `src/yggdrasil/ratatosk/agent.py` | depth expand | L0–L3 algorithm reference |
| `docs/plans/RATATOSK-SPEC-REALIGNMENT-PLAN.md` | A5 | Budget default 8000 |
| `ratatosk/config.py` | budget key | CFG-02 override path |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT inject full graph into prompt — summary only.
- Do NOT omit blackboard key when model empty (chars may be small but key present).

---

## SAO.md Sections That Apply

- A5 ModelSummary depth expansion

---

## Current State Assessment

Runner may log `fetching existing model state` instead of building summary; blackboard key **likely missing**.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc15_blackboard_has_model_summary_chars` | integration | key exists, int > 0 |
| `test_disc15_summary_under_budget` | integration | value <= 8000 * chars_per_token_estimate |
| `test_disc15_empty_model_summary_nonzero_key` | integration | empty graph still records key |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| ModelSummary builder | entry | budget_tokens, model_slug |
| ModelSummary builder | exit | chars_used, depth_reached, budget_remaining |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Implement ModelSummary builder with char/token counter.
2. Write `blackboard["model_summary_chars"]` after build.
3. Red test on key presence and cap.
4. Align log phrase to `building ModelSummary`.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc15_blackboard_has_model_summary_chars -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `And the run blackboard model_summary_chars is at most {n:d} tokens equivalent` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
