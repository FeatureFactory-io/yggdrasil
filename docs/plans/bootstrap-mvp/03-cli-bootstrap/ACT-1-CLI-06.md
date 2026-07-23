# ACT-1-CLI-06 — Bootstrap with missing token fails with clear error

**Tier:** 3 (error hygiene)
**Wave:** W9
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** `ratatosk/cli.py` `_require_token`
**Canonical index:** [09-error-hygiene](../09-error-hygiene/README.md)

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-06 Bootstrap with missing token fails with clear error
  When Priya runs:
    """
    ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4
    """
  Then the exit code is not 0
  And the output contains "token"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 30–35 | `_require_token` — exit 2, stderr message |
| `ratatosk/cli.py` | 75–85 | bootstrap calls `_require_token` before MCP |
| `docs/features/steps/cli_steps.py` | token steps | Mirror DISC-07 phrasing |
| `ratatosk/tests/test_cli_click.py` | new | Click runner isolation |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT attempt MCP calls without token — fail before network.
- Do NOT print token format hints that leak validation rules.

---

## SAO.md Sections That Apply

- §18.5 Auth — PAT required for write handoff

---

## Current State Assessment

| Piece | State |
|-------|--------|
| `_require_token` | Exists — message contains `--token` |
| Exit code | 2 today — scenario accepts `not 0` |
| DISC-07 duplicate | Same behavior via discovery feature — keep one implementation, two AT scenarios |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_cli_bootstrap_missing_token` | unit Click | exit ≠ 0, stderr contains `token` |
| `test_cli_bootstrap_no_mcp_calls_without_token` | unit mock | McpClient never constructed |
| `test_cli06_behave` | behave | Gherkin When/Then |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `ratatosk.cli.bootstrap` | token missing | reason=missing_token, exit_code=2 |
| `_require_token` | reject | user_message_preview (no secrets) |

---

## MCP Tools to Expose

Not applicable — fails before MCP.

---

## Implementation Steps

1. **Red:** `test_cli_bootstrap_missing_token` — may already pass if `_require_token` wired.
2. **Green:** Ensure bootstrap invokes `_require_token` before `RatatoskMcpClient`.
3. **Green:** Log INFO on reject path (who=anonymous, why=missing_token).
4. **Green:** Behave step shares implementation with DISC-07.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_cli_bootstrap_missing_token -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya runs:` (no token) | `cli_steps.py` |
| `Then the exit code is not 0` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
