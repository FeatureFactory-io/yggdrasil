# ACT-1-CFG-09 — YGGDRASIL_SERVER_URL default for CLI bootstrap server

**Tier:** 1
**Wave:** W1
**Feature file:** `docs/features/act-1-ratatosk/ratatosk-config.feature`
**Package:** `01-config/`
**Depends on:** ACT-1-CFG-06
**Blocks:** ACT-1-CLI-09, ACT-1-DISC-21

---

## Scenario (Gherkin)

```gherkin
Scenario: ACT-1-CFG-09 YGGDRASIL_SERVER_URL default for CLI bootstrap server
  Given the environment variable "YGGDRASIL_SERVER_URL" is set to "http://localhost:8000"
  When Ratatosk loads configuration for bootstrap
  Then the effective config key "yggdrasil_server_url" is "http://localhost:8000"
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ratatosk/cli.py` | 65–71 | `--server` default is cloud URL; env var overrides via Click |
| `ratatosk/mcp_client.py` | all | `RatatoskMcpClient(server=...)` base URL for tool POSTs |
| `docs/features/user_journey.md` | 153 | Certification uses local server |

---

## Do Not Do

Do NOT hardcode localhost in production default — cloud default remains when env unset; scenario tests explicit local env for dev certification.

---

## Current State Assessment

- Click already binds `YGGDRASIL_SERVER_URL` to `--server`.
- Missing: config loader exposes merged effective URL for behave; DISC-21 needs assert MCP hits localhost not cloud.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_load_config_yggdrasil_server_url_from_env` | unit | effective URL |
| `test_cli_server_flag_overrides_env` | unit | `--server` wins over env per merge order |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `RatatoskMcpClient.__init__` | init | server base URL (no token) |
| `RatatoskMcpClient.call_tool` | each call | tool name, HTTP status |

---

## Implementation Steps

1. Add `yggdrasil_server_url` to `BootstrapConfig`.
2. Merge: CLI flag > env > default cloud.
3. Pass to `RatatoskMcpClient` in bootstrap command.
4. Behave step validates effective key.

---

## Checkpoint

```bash
pytest ratatosk/tests/test_config_loader.py::test_load_config_yggdrasil_server_url_from_env -x
```

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
