# ACT-1-CLI-02 — Re-bootstrap wipes graph then scans with instructions

> **DEFER (Tier 4)** — Implement after W0–W9 green. Wave package: [10-rebootstrap](README.md).

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `10-rebootstrap/`
**Implementation detail:** [03-cli-bootstrap/ACT-1-CLI-02.md](../03-cli-bootstrap/ACT-1-CLI-02.md)
**Depends on:** W9 green, populated graph fixture (31 elements, 44 relationships)

---

## Scenario (Gherkin)

```gherkin
@wip
Scenario: ACT-1-CLI-02 Re-bootstrap wipes graph then scans with instructions
  When Priya runs ratatosk bootstrap ... --instructions "Do an extra pass..."
  Then output contains "wiping 31 elements and 44 relationships"
  And "scanning ./repo with instructions"
  And output does not contain "unchanged:"
```

---

## Wave-specific analysis

Re-bootstrap is the **policy correction** scenario from RATATOSK-SPEC-REALIGNMENT-PLAN: journey transcript previously showed delta merge (`unchanged: 22`) — wrong. This scenario locks stdout to wipe-then-fresh-scan semantics and proves `--instructions` appear in scan log for Munin/Ratatosk context.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | wipe + scan | Bulk wipe MCP call |
| `ratatosk/cli.py` | `--instructions` | Forward to runner |
| `tests/fixtures/graph/populated_31_44.json` | seed | Counts for wipe message |
| `docs/features/user_journey.md` | Act 1 | Narrative alignment |

---

## Do Not Do

Inherit SHARED-CONTRACT — wipe via MCP; no incremental reconcile on bootstrap.

---

## SAO.md Sections That Apply

- §17.3 re-bootstrap
- A3.8 bulk wipe

---

## Current State Assessment

Wipe on populated model not implemented; instructions not echoed in scan line.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_rebootstrap_wipe_message_counts` | subprocess | 31/44 in stdout |
| `test_rebootstrap_instructions_in_scan_log` | subprocess | instructions substring |
| `test_rebootstrap_no_unchanged` | subprocess | negative assert |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| wipe | bulk | element_count, relationship_count |
| scan | start | has_instructions, instructions_preview |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `bulk_wipe_model` | Pre-scan graph clear |

---

## Implementation Steps

1. Seed 31/44 fixture after W9.
2. Implement bulk wipe + stdout (see 03-cli-bootstrap plan).
3. Run W10+ gate: all three tests green.
4. Update behave @wip tags.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_rebootstrap_wipe_message_counts -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given ... 31 elements and 44 relationships` | `discovery_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
