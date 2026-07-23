# ACT-5-MCP-CHANGESET-04 — reject with reason appends LEARNED rule

> **DEFER (Tier 4)** — Implement after W0–W9 green. Requires Munin LEARNED prompt layer.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`

---

## Scenario (Gherkin)

```gherkin
When Marcus calls reject_changeset id=1 item_ids [3] reason "Code diagram..."
Then operation 3 rejected, MuninRule created, prepended to BASE prompt
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/munin/` | MuninRule | LEARNED storage |
| `src/yggdrasil/changeset/services.py` | reject partial | reason param |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- Munin LEARNED rules (SAO Munin section)

---

## Current State Assessment

MuninRule model may not exist — Part II feature.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_reject_creates_munin_rule` | integration | rule text matches reason |
| `test_learned_prepended_next_run` | integration | prompt contains rule |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `reject_changeset` | rule created | rule_id, reason_len |

---

## MCP Tools to Expose

| Tool | Change |
|------|--------|
| `reject_changeset` | `reason`, optional `item_ids` |

---

## Implementation Steps

1. MuninRule model + service.
2. reject_changeset creates rule on reason.
3. MuninAgent loads LEARNED on next invoke.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py::test_reject_creates_munin_rule -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
