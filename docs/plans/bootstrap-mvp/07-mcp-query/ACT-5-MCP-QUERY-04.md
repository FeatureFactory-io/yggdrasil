# ACT-5-MCP-QUERY-04 — traverse returns incoming dependencies

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** ACT-1-CLI-04 (relationship ops applied)

---

## Scenario (Gherkin)

```gherkin
When Priya calls MCP tool "traverse" with from payment-api, direction incoming
Then the response contains "Mobile App" and "Order Domain"
And each entry includes owner and confidence
```

---

## Why this scenario matters

Proves bootstrap **relationship graph is queryable** via MCP — the payoff for Munin linking. Without CLI-04 edges, traverse returns empty and Act 5 certification fails.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | traverse | Direction incoming/outgoing |
| `src/yggdrasil/graph/services.py` | traverse | Graph walk |
| `tests/integration/test_journey_bootstrap_then_update.py` | extend | Post-bootstrap traverse |

---

## Do Not Do

Inherit SHARED-CONTRACT — traverse is read-only.

---

## SAO.md Sections That Apply

- §18.4 traverse
- A5.6 scout may call traverse

---

## Current State Assessment

Relationships from Munin planner must exist in seed or post-CLI-04 bootstrap fixture.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_traverse_incoming_payment_api` | integration | Mobile App + Order Domain |
| `test_traverse_entry_has_owner_confidence` | integration | per-entry fields |
| `test_traverse_unknown_slug_404` | integration | error hygiene |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `traverse` | entry | from_slug, direction |
| `traverse` | exit | edge_count, sample_targets |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `traverse` | GraphQueryService.traverse | No |

---

## Implementation Steps

1. Bootstrap fixture with known edges into Payment API.
2. Red traverse incoming test.
3. Green response shape with owner/confidence on each neighbor.
4. Link to L1 journey extension test.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_traverse_incoming_payment_api -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "traverse" with:` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-not-mock-in-integration-tests.mdc
- do-informative-logging.mdc
