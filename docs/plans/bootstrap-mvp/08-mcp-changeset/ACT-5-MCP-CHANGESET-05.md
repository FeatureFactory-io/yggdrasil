# ACT-5-MCP-CHANGESET-05 — do_other_changeset redirects Munin re-plan

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-5-mcp/mcp-changeset.feature`
**Package:** `08-mcp-changeset/`

---

## Scenario (Gherkin)

```gherkin
When Marcus calls do_other_changeset id=1 item_ids [3] instructions "don't add..."
Then op 3 rejected, Munin re-processes, replacement ChangeSet, instructions in LEARNED
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/munin/agent.py` | re-plan | Redirect flow |
| `src/yggdrasil/mcp/tools/changeset.py` | do_other_changeset | May be missing |

---

## Do Not Do

Inherit SHARED-CONTRACT — re-plan still through ChangeSet pipeline.

---

## SAO.md Sections That Apply

- Munin redirect workflow (user journey Act 5)

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_do_other_changeset_replacement_cs` | integration | new CS with corrected op |
| `test_do_other_learned_append` | integration | instructions in LEARNED |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `do_other_changeset` | entry | item_ids, instructions_len |
| MuninAgent | re-plan | original_item_id, replacement_cs_id |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `do_other_changeset` | MuninRedirectService | Yes |

---

## Implementation Steps

1. Register MCP tool.
2. Reject specified items + invoke Munin with instructions.
3. Create replacement ChangeSet.
4. Append LEARNED.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_approve_changeset.py::test_do_other_changeset_replacement_cs -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
