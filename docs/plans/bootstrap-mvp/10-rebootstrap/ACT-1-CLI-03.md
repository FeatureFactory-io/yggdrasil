# ACT-1-CLI-03 — Bootstrap output shows add-heavy buckets after wipe

> **DEFER (Tier 4)** — Implement after W0–W9 green. Wave package: [10-rebootstrap](README.md).

**Tier:** 4
**Wave:** W10+
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `10-rebootstrap/`
**Implementation detail:** [03-cli-bootstrap/ACT-1-CLI-03.md](../03-cli-bootstrap/ACT-1-CLI-03.md)
**Depends on:** ACT-1-CLI-02

---

## Scenario (Gherkin)

```gherkin
@wip
Scenario: ACT-1-CLI-03 Bootstrap output shows add-heavy buckets after wipe
  Given Priya has run a bootstrap with new candidates discovered
  Then output contains "to_add:"
  And output does not contain "unchanged:" or "to_update:"
```

---

## Wave-specific analysis

Validates **bucket printer mode** for post-wipe bootstrap: only `to_add` is meaningful. Shared reconcile code with `ratatosk update` must branch on `mode=bootstrap_post_wipe`.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/discovery/runner.py` | buckets | bootstrap vs update mode |
| `src/yggdrasil/ratatosk/agent.py` | reconcile | Shared logic |

---

## Do Not Do

Inherit SHARED-CONTRACT.

---

## SAO.md Sections That Apply

- A3.6 unchanged not meaningful post-wipe

---

## Current State Assessment

Update reconcile may leak unchanged/to_update into bootstrap stdout.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_bootstrap_buckets_add_only_stdout` | integration | negative unchanged/to_update |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| reconcile | exit | mode=bootstrap_post_wipe, buckets emitted |

---

## MCP Tools to Expose

Not applicable.

---

## Implementation Steps

1. Implement reconcile mode flag (CLI-02 branch).
2. Red stdout assertions.
3. Composite behave Given after CLI-02 run.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_bootstrap_buckets_add_only_stdout -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
