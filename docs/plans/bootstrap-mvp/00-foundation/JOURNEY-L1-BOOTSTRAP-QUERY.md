# JOURNEY-L1-BOOTSTRAP-QUERY — North-star integration

**Type:** Foundation work item (not a Gherkin scenario ID)
**Tier:** W0
**Wave:** W0
**Depends on:** [SHARED-CONTRACT.md](SHARED-CONTRACT.md), MCP propose tools (partially exist)
**Blocks:** Confidence that W4–W7 modules integrate before subprocess CLI certification

---

## Purpose

Single programmatic integration test proving:

1. Act 1 bootstrap on `sample_webapp` via **in-process MCP tool callables** (same functions production MCP registers).
2. ChangeSet created with `source=ratatosk`, no orphan Elements.
3. Auto-apply above 0.80 leaves elements on graph (no manual approve on happy path).
4. Act 6 stdin update produces second ChangeSet without wipe.
5. *(Extend)* MCP `list_elements` returns manifest names; `traverse` shows relationships after CLI-04 lands.

File today: `tests/integration/test_journey_bootstrap_then_update.py`.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `tests/integration/test_journey_bootstrap_then_update.py` | 48–117 | Existing L1 — bootstrap + update only |
| `src/yggdrasil/ratatosk/inprocess_mcp.py` | 20–70 | `InProcessMcpToolClient` — journey must use this, not LocalOrm |
| `src/yggdrasil/ratatosk/agent.py` | 530–620 | `bootstrap_repository`, `update_from_stdin` |
| `src/yggdrasil/mcp/tools/query.py` | list/traverse | Extend journey asserts post-W6 |
| `tests/fixtures/repos/sample_webapp/` | all | Fixture repo + `expected_elements.yaml` |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT use Playwright or HTTP for this test — in-process MCP only.
- Do NOT use `LocalOrmHandoffPort` in journey — must exercise `McpHandoffPort` + in-process tools to match DISC-21 intent.
- Do NOT assert relationship traverse until CLI-04 Munin planner exists — mark extension TODO with skip.

---

## Current State Assessment

### Exists

- `test_journey_bootstrap_then_update_via_mcp` with orphan check, two ChangeSets, MCP handoff ports.
- ScriptedDiscoveryLLM returns 4 manifest-aligned candidates.

### Gaps

- Output still expects legacy log phrase `fetching existing model state via MCP` (runner), not journey transcript `building ModelSummary`.
- No QUERY assertions (`list_elements`, `traverse`).
- Relationship count likely zero until CLI-04 — document as staged assertion.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_journey_bootstrap_then_update_via_mcp` | integration L1 | *(exists)* two changesets, no orphans |
| `test_journey_bootstrap_list_elements_manifest` | integration L1 | after bootstrap, `list_elements` contains Payment API, Order Service, Order Domain, Billing Worker |
| `test_journey_bootstrap_traverse_relationships` | integration L1 | after CLI-04: traverse incoming to Payment API non-empty |
| `test_journey_no_manual_approve_on_happy_path` | integration L1 | applied ChangeSetItem count > 0 before any approve call |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `test_journey_*` setup | user + model create | user_id, model slug |
| `InProcessMcpToolClient.call_tool` | each tool | tool name, model slug, op count for propose |
| `_assert_no_orphans` | failure | element name without ChangeSetItem |

---

## MCP Tools to Expose

Uses existing tools — no new registration. Journey validates:

| Tool | Write? | Used in journey |
|------|--------|-----------------|
| `ensure_model` | Yes | bootstrap start |
| `list_elements` | No | snapshot + QUERY assert |
| `list_relationships` | No | snapshot |
| `list_stereotypes` | No | guidance |
| `propose_changeset` | Yes | handoff |
| `record_ratatosk_run` | Yes | blackboard persist |
| `list_elements` | No | post-bootstrap QUERY extension |

---

## Implementation Steps

1. **Red:** Add `test_journey_bootstrap_list_elements_manifest` expecting 4 names — will fail until auto-apply + element ops correct.
2. **Green:** Ensure journey uses confidence 0.80 and scripted candidates all ≥ 0.80.
3. **Green:** After W4 runner alignment, update log phrase assertion to accept `building ModelSummary`.
4. **After W6:** Add traverse assertion with known Munin-planned edge (Order Domain → Payment API or similar from sample_webapp README).
5. **Refactor:** Split helpers `_bootstrap_sample_webapp(user)` shared with MCP tool tests.

---

## Checkpoint

```bash
pytest tests/integration/test_journey_bootstrap_then_update.py -x
```

Expected: all tests in file green including QUERY extension when scheduled.

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-small-increments.mdc
- do-informative-logging.mdc
