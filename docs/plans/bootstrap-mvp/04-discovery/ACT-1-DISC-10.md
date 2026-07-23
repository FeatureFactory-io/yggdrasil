# ACT-1-DISC-10 — Metamodel mismatch on existing Model fails

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-10 Metamodel mismatch on existing Model fails
  Given ... model exists bound to metamodel "c4"
  When ... with metamodel "other"
  Then the exit code is not 0
  And the output contains "bound to metamodel"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/graph/models.py` | YggdrasilModel | Immutable metamodel FK |
| `src/yggdrasil/mcp/tools/` | ensure_model | Mismatch detection |

---

## Do Not Do

Inherit SHARED-CONTRACT — never rebind model metamodel from CLI.

---

## SAO.md Sections That Apply

- A1.1 multiple Metamodel rows, one binding per model

---

## Current State Assessment

Need explicit check when CLI `--metamodel` ≠ model's bound slug.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc10_metamodel_mismatch` | integration | message bound to metamodel |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| ensure_model | mismatch | model_slug, bound=c4, requested=other |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `ensure_model` | Returns 400 on mismatch |

---

## Implementation Steps

1. Seed model with c4.
2. Bootstrap with --metamodel other.
3. Fail before scan.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_disc10_metamodel_mismatch -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
