# ACT-1-CLI-09 — Bootstrap uses local server URL from environment

**Tier:** 1
**Wave:** W5
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-bootstrap.feature`
**Package:** `03-cli-bootstrap/`
**Depends on:** ACT-1-CFG-09, ACT-1-DISC-21
**Blocks:** Local docker-compose certification

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CLI-09 Bootstrap uses local server URL from environment
  Given ... YGGDRASIL_SERVER_URL ... "http://localhost:8000"
  When Priya runs ratatosk bootstrap ... --server http://localhost:8000
  Then the exit code is 0
  And the output contains "run complete"
```

---

## Why this scenario matters

Default CLI `--server` points at production URL (`yggdrasil.featurefactory.io`). Local MVP requires **env + flag** to hit `localhost:8000` without code edits. CFG-09 proves config merge; CLI-09 proves the merged URL reaches `RatatoskMcpClient` HTTP calls.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 65–71 | `--server` + `YGGDRASIL_SERVER_URL` envvar |
| `ratatosk/config.py` | merge | CFG-09 effective key (W1) |
| `ratatosk/mcp_client.py` | base URL | Must not hardcode production host |
| `ratatosk/tests/test_config_loader.py` | CFG-09 | Config unit tests |
| `tests/integration/mcp_harness/` | fixtures | Local MCP server for subprocess |

---

## Do Not Do

Inherit SHARED-CONTRACT, plus:

- Do NOT ignore `--server` when env is also set — flag wins per merge order.
- Do NOT log full PAT or server credentials.

---

## SAO.md Sections That Apply

- §18.5 Auth — Bearer to configured server base URL

---

## Current State Assessment

| Piece | State |
|-------|--------|
| Click `--server` option | Exists with envvar default |
| Config module `yggdrasil_server_url` | W1 — may duplicate Click default |
| Subprocess hitting localhost | Needs test harness on port 8000 or dynamic |

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_cli_bootstrap_uses_server_flag` | unit/mock transport | HTTP requests go to localhost base |
| `test_cli_bootstrap_env_server_url` | unit | env default when flag omitted |
| `test_cli09_subprocess_local_server` | integration | run complete against harness |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `RatatoskMcpClient.__init__` | entry | base_url (host only), tool_prefix |
| `ratatosk.cli.bootstrap` | MCP call | tool_name, server_host |

---

## MCP Tools to Expose

Not applicable — client configuration only.

---

## Implementation Steps

1. **Red:** Mock transport asserts host `localhost:8000` when env+flag set.
2. **Green:** Wire config loader output into Click default if CFG-09 merged.
3. **Green:** Subprocess test with ephemeral Django test server or mcp_harness.
4. **Refactor:** Single `_resolve_server_url(flag, env, config)` helper.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_cli_click.py::test_cli_bootstrap_uses_server_flag -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `Given the environment variable "YGGDRASIL_SERVER_URL" is set to "{url}"` | `cli_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
