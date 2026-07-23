# ACT-1-DISC-02 — Blackboard records tree paths before extract

**Tier:** 1
**Wave:** W4
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`
**Depends on:** W0 runner skeleton
**Blocks:** ACT-1-DISC-01, ACT-1-DISC-15

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-02 Blackboard records tree paths before extract
  ...
  Then the run blackboard contains step "tree"
  And the run blackboard tree includes "docker-compose.yml"
  And the run blackboard tree includes "src/order_service/app.py"
  And the run blackboard tree includes "src/billing_worker/worker.py"
  And the run blackboard contains step "extract"
```

---

## Why this scenario matters

Blackboard ordering proves **filesystem scan precedes LLM extract** — observable evidence for debugging "wrong candidates" without re-running Ollama. Step keys `tree` then `extract` are AT contract for scout/bootstrap parity.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | tree walk | Records paths to blackboard |
| `tests/fixtures/repos/sample_webapp/` | tree | Known files in scenario |
| `src/yggdrasil/ratatosk/models.py` | blackboard JSON | Persisted on RataskRun |
| `src/yggdrasil/ratatosk/agent.py` | blackboard init | Step sequencing |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT run extract before tree step recorded.
- Do NOT store full file contents in blackboard tree — paths only.

---

## SAO.md Sections That Apply

- §17.3 bootstrap pipeline steps

---

## Current State Assessment

Tree walk likely exists; blackboard step keys may use different names — align to `tree` and `extract` strings exactly.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc02_blackboard_tree_step_first` | integration | step order tree before extract |
| `test_disc02_tree_includes_compose_and_services` | integration | three path substrings |
| `test_disc02_behave` | behave | Gherkin paths |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| tree walk | entry | repo_root, ignore_patterns |
| tree walk | exit | path_count, sample_paths_head |
| extract | entry | prior_step=tree |

---

## MCP Tools to Expose

Not applicable (blackboard local until record_ratatosk_run).

---

## Implementation Steps

1. **Red:** Assert blackboard `steps` list contains `tree` before `extract`.
2. **Green:** Normalize step key names in runner.
3. **Green:** Store relative paths from repo root in `blackboard["tree"]`.
4. **Green:** Verify sample_webapp fixture paths exist on disk in test setup.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc02_blackboard_tree_step_first -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Then the run blackboard contains step "{step}"` | `discovery_steps.py` |
| `And the run blackboard tree includes "{path}"` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
