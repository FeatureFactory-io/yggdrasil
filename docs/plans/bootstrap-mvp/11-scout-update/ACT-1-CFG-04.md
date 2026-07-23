# ACT-1-CFG-04 — Secrets resolve from env:VAR only

> **DEFER (Tier 4)** — Implement after W0–W9 green.

**Tier:** 4 | **Wave:** W10+ | **Feature:** `ratatosk-config.feature`

## Scenario (Gherkin)
```gherkin
Given ratatosk.yaml atlassian token "env:ATLASSIAN_TOKEN" and env set
When load configuration for update
Then token resolved from environment; repo file has no plaintext secret
```

## Context Map
| File | Lines | Note |
|------|-------|------|
| `ratatosk/config.py` | secret resolver | env: prefix |
| `tests/fixtures/ratosk.yaml` | sample | No plaintext tokens |

## Do Not Do
Inherit SHARED-CONTRACT — never commit secrets in repo YAML.

## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_cfg04_env_var_secret_resolution` | unit | resolved value from os.environ |

## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| load_config | secret resolve | key_name, source=env (not value) |

## MCP Tools to Expose
Not applicable.

## Implementation Steps
1. Implement env:VAR resolver for string values ending with env prefix pattern.
2. Fail if env missing with clear error.
3. Assert repo fixture file contains env: not literal token.

## Checkpoint
`pytest ratatosk/tests/test_config_loader.py::test_cfg04_env_var_secret_resolution -x`

## Rules Applied
do-test-first.mdc, do-informative-logging.mdc
