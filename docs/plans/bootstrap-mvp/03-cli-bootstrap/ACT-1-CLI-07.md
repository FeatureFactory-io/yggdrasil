# ACT-1-CLI-07 — Bootstrap uses existing C4 Metamodel ontology

**Tier:** 1
**Wave:** W5
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** ACT-1-CLI-01, ACT-1-DISC-01, seed C4 metamodel
**Blocks:** ACT-5-MCP-QUERY-09

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-07 Bootstrap uses existing C4 Metamodel ontology
  Given the Metamodel "c4" exists with C4 stereotypes and packages
  And a successful bootstrap run on a Python web application repository
  Then the model's metamodel is "c4"
  And the model contains elements with stereotypes from: Container, Component, System
  And the model's metamodel contains packages from: Context, Technology, Application
```

---

## Why this scenario matters

Bootstrap must **bind to existing C4 ontology** — not invent ad-hoc stereotypes or packages. This scenario validates end-state graph + metamodel catalog after CLI-01 happy path, proving `ensure_c4_metamodel()` seed data flows through discovery cleanup into applied ChangeSet items.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/graph/management/` | ensure_c4 | C4 seed stereotypes/packages |
| `src/yggdrasil/ratatosk/agent.py` | metamodel guidance | `_metamodel_guidance()` text |
| `ratatosk/discovery/runner.py` | cleanup | Drops unknown stereotypes (DISC-04) |
| `tests/fixtures/repos/sample_webapp/expected_elements.yaml` | all | Manifest stereotypes map to C4 |
| `src/yggdrasil/mcp/tools/query.py` | list_stereotypes | Post-bootstrap catalog check |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT create new Metamodel rows during bootstrap — use slug `c4`.
- Do NOT accept LLM-invented stereotypes on the graph (see DISC-04).

---

## SAO.md Sections That Apply

- §17.3 — metamodel guidance in user message
- Metamodel binding — model immutable metamodel FK

---

## Current State Assessment

| Piece | State |
|-------|--------|
| C4 seed in tests | Via fixtures / `ensure_c4_metamodel` |
| sample_webapp manifest | 4 elements — Container/Component only (no System in repo) |
| System stereotype in scenario table | May need journey seed element or adjust assertion to manifest |

**Clarification:** Scenario table lists `System` — sample_webapp manifest has no System element. Plan: assert **metamodel catalog** contains System stereotype; graph may only show Container/Component from fixture unless seed adds Mobile App for query tier.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_cli07_model_metamodel_slug_c4` | integration | model.metamodel.slug == c4 |
| `test_cli07_elements_use_c4_stereotypes` | integration | each element stereotype in C4 set |
| `test_cli07_metamodel_packages_present` | integration | Context, Technology, Application packages exist |
| `test_cli07_behave_post_bootstrap` | behave | Given successful bootstrap run step |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ensure_model` MCP | bind | model_slug, metamodel_slug |
| runner metamodel step | guidance | stereotype_count, package_count |
| cleanup | reject unknown | stereotype, action=dropped |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `list_stereotypes` | Verify catalog post-bootstrap |
| `list_elements` | Verify applied element stereotypes |

---

## Implementation Steps

1. **Red:** After CLI-01 subprocess, query ORM/MCP for metamodel FK = c4.
2. **Green:** Assert manifest elements match C4 stereotypes (case-normalized).
3. **Green:** Query metamodel packages — Context, Technology, Application present.
4. **Green:** Behave `Given a successful bootstrap run` composite step reusing CLI-01.
5. **Refactor:** Shared fixture `bootstrapped_sample_webapp` for CLI-07 and QUERY tier.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_cli07_model_metamodel_slug_c4 -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given a successful bootstrap run on a Python web application repository` | `cli_steps.py` |
| `Then the model's metamodel is "{slug}"` | `discovery_steps.py` |
| `And the model contains elements with stereotypes from:` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
