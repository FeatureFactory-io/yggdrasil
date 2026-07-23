# Package 09 — Error Hygiene

Tier 3 scenarios — fail-fast, clear messages, no silent graph corruption. Wave W9 after W7–W8.

**Gate:** Per-scenario checkpoints below (aggregate green before W10+).

## Canonical plan paths (do not duplicate — link only)

| ID | Message contract | Plan file | Checkpoint |
|----|------------------|-----------|------------|
| ACT-1-CLI-06 | output contains `token` | [03-cli-bootstrap/ACT-1-CLI-06.md](../03-cli-bootstrap/ACT-1-CLI-06.md) | `pytest ratatosk/tests/test_cli_click.py::test_cli_bootstrap_missing_token -x` |
| ACT-1-DISC-04 | no unknown stereotype on graph | [04-discovery/ACT-1-DISC-04.md](../04-discovery/ACT-1-DISC-04.md) | `pytest ...::test_disc04_drops_microservice_stereotype -x` |
| ACT-1-DISC-05 | LLM invoked, no hardcode | [04-discovery/ACT-1-DISC-05.md](../04-discovery/ACT-1-DISC-05.md) | `pytest ...::test_disc05_llm_invoked_with_scripted_provider -x` |
| ACT-1-DISC-07 | output contains `token` | [04-discovery/ACT-1-DISC-07.md](../04-discovery/ACT-1-DISC-07.md) | same as CLI-06 |
| ACT-1-DISC-08 | `permission`, no ChangeSet | [04-discovery/ACT-1-DISC-08.md](../04-discovery/ACT-1-DISC-08.md) | `pytest ...::test_disc08_readonly_token_exit_nonzero -x` |
| ACT-1-DISC-11 | `path`, no ChangeSet | [04-discovery/ACT-1-DISC-11.md](../04-discovery/ACT-1-DISC-11.md) | `pytest ...::test_disc11_missing_repo_path -x` |
| ACT-1-DISC-13 | `MCP`, no orphan | [04-discovery/ACT-1-DISC-13.md](../04-discovery/ACT-1-DISC-13.md) | `pytest tests/integration/mcp_harness/test_disc13_mcp_unreachable.py -x` |
| ACT-1-DISC-14 | empty plan message | [04-discovery/ACT-1-DISC-14.md](../04-discovery/ACT-1-DISC-14.md) | `pytest ...::test_disc14_non_json_empty_plan_message -x` |
| ACT-1-LLM-02 | output contains `model` | [02-ollama-llm/ACT-1-LLM-02.md](../02-ollama-llm/ACT-1-LLM-02.md) | `pytest src/yggdrasil/llm/tests/test_ollama_client.py -k model_not -x` |
| ACT-1-LLM-04 | no microservice stereotype | [02-ollama-llm/ACT-1-LLM-04.md](../02-ollama-llm/ACT-1-LLM-04.md) | `pytest ...::test_llm04_fenced_json_stereotype_filter -x` |

## Shared hygiene rules

Inherit [SHARED-CONTRACT](../00-foundation/SHARED-CONTRACT.md):

- Reject paths log **who / what / why** at INFO before exit.
- Never log PAT or raw LLM prompts.
- Integration tests use real DB — no mock ORM for orphan checks.
- Every reject path: assert **no orphan Elements** where scenario specifies.

## W9 execution order

1. Token/path auth errors (CLI-06, DISC-07, DISC-11) — cheap Click tests.
2. MCP auth (DISC-08, DISC-13) — harness failures.
3. LLM hygiene (DISC-04, DISC-05, DISC-14, LLM-02, LLM-04) — scripted injects.
4. Full W9 gate: run all checkpoint commands in table sequentially.

## Logging verification

Before closing W9, grep `logs/app.log` from each test run for the **Logs to Emit** rows in each canonical plan — missing INFO lines are checkpoint FAIL.
