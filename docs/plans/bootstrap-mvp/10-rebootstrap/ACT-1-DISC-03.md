# ACT-1-DISC-03 — Re-bootstrap bulk-wipes existing graph before rescan

> **DEFER (Tier 4)** — Implement after W0–W9 green. Wave package: [10-rebootstrap](README.md).

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-discovery.feature`
**Package:** `10-rebootstrap/`
**Implementation detail:** [04-discovery/ACT-1-DISC-03.md](../04-discovery/ACT-1-DISC-03.md)
**Depends on:** ACT-1-CLI-02

---

## Scenario (Gherkin)

```gherkin
@wip
Scenario: ACT-1-DISC-03 Re-bootstrap bulk-wipes existing graph before rescan
  Given model exists with element "Payment API"
  When bootstrap against sample_webapp
  Then output contains "wiping" and "to_add:", not "unchanged:"
```

---

## Wave-specific analysis

Same wipe policy as CLI-02 but proven via **in-process** `bootstrap_repository` + behave discovery steps — catches runner bugs without subprocess noise.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/ratatosk/agent.py` | bootstrap_repository | In-process entry |
| `ratatosk/discovery/runner.py` | shared wipe | Called from agent + CLI |

---

## Do Not Do

Inherit SHARED-CONTRACT — even in-process handoff uses ChangeSet pipeline after wipe.

---

## SAO.md Sections That Apply

- §17.3 bootstrap wipe

---

## Current State Assessment

Feature file @wip; DISC-03 was historically delta semantics — must rewrite step expectations.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_disc03_inprocess_wipe_then_rescan` | integration | in-process stdout/log capture |

---

## Logs to Emit

Same as ACT-1-CLI-02 wipe logs.

---

## MCP Tools to Expose

| Tool | Role |
|------|------|
| `bulk_wipe_model` | Via McpHandoffPort in subprocess; ORM admin op in in-process test setup |

---

## Implementation Steps

1. Share wipe module between CLI and agent paths.
2. In-process test with pre-seeded Payment API.
3. Remove @wip when CLI-02 green.

---

## Checkpoint

```bash
pytest src/yggdrasil/ratatosk/tests/test_discovery_agent.py::test_disc03_inprocess_wipe_then_rescan -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `And the output contains "wiping"` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
