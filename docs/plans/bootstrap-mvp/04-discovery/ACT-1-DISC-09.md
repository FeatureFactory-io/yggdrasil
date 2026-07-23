# ACT-1-DISC-09 — Unknown metamodel slug fails

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `04-discovery/`

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-DISC-09 Unknown metamodel slug fails
  When ... with metamodel "no-such-mm"
  Then the exit code is not 0
  And the output contains "metamodel"
  And no Model was created with metamodel "no-such-mm"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | `--metamodel` | Validated via MCP ensure_model |
| `src/yggdrasil/mcp/tools/` | ensure_model | Rejects unknown slug |

---

## Do Not Do

Inherit SHARED-CONTRACT — do not auto-create metamodel rows from CLI.

---

## SAO.md Sections That Apply

- Metamodel binding immutability

---

## Current State Assessment

ensure_model behavior for unknown slug — verify fail-fast.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc09_unknown_metamodel` | integration | exit ≠ 0, no model row |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| ensure_model | reject | metamodel_slug, reason=not_found |

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `ensure_model` | Validates metamodel exists |

---

## Implementation Steps

1. Call ensure_model with no-such-mm.
2. Map error to CLI stderr.
3. Assert no YggdrasilModel created with bad FK.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_disc09_unknown_metamodel -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
