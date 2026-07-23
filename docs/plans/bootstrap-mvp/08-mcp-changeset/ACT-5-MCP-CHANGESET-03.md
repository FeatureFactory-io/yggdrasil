# ACT-5-MCP-CHANGESET-03 — reject_changeset rejects all pending

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`

---

## Scenario (Gherkin)

```gherkin
When Priya calls reject_changeset id=1
Then all 6 rejected, status "rejected"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/changeset/services.py` | reject | |
| `src/yggdrasil/mcp/tools/changeset.py` | reject_changeset | |

---

## Do Not Do

Inherit SHARED-CONTRACT — reject must not apply ops to graph.

---

## SAO.md Sections That Apply

- §18.4 reject_changeset

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_reject_changeset_all_pending` | integration | status rejected, graph unchanged |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `reject_changeset` | exit | rejected_count, status=rejected |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `reject_changeset` | ChangeSetService.reject | Yes |

---

## Implementation Steps

1. Implement reject service + MCP tool if missing.
2. Red integration test.
3. Behave.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py::test_reject_changeset_all_pending -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
