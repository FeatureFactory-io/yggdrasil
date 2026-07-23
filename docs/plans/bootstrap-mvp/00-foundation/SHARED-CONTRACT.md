# SHARED-CONTRACT — Bootstrap MVP program constraints

Every scenario plan under `docs/plans/bootstrap-mvp/` inherits this document.
Scenario-specific **Do Not Do** rows are additive only.

**Branch for implementation:** `feature/bootstrap-mvp-w1` from `main`.

---

## Do Not Do (program-wide)

- Do NOT create a new Django app.
- Do NOT write Elements or Relationships from the Ratatosk CLI via ORM — production path is HTTP MCP only.
- Do NOT call `django.setup()` in production `ratatosk bootstrap` or `ratatosk update`.
- Do NOT bypass the ChangeSet pipeline (no direct graph writes from CLI, MCP tools, or agents).
- Do NOT let Ratatosk invent relationships — Munin owns relationship ops (SAO §17.3).
- Do NOT reintroduce silent Payment API hardcoded candidates except when `LLM_PROVIDER=scripted` and `ScriptedDiscoveryLLM` is explicitly selected.
- Do NOT mock the database in integration tests that prove orphan-element or ChangeSet invariants (Fake MCP client is OK for CLI unit tests only).
- Do NOT modify root `settings.py`, root `urls.py`, or `pyproject.toml` dependencies without a human `status-blocked` note.
- Do NOT create GitHub issues during planning or W0–W9 implementation — PIN playbook produces issues later.
- Do NOT use `set_model_mode` or admin shortcuts to bypass ChangeSet review for bootstrap certification.

---

## SAO.md sections that apply (all bootstrap/MCP work)

- **§1 Dependency rules** — `ratatosk` package is a remote MCP client; server owns graph + ChangeSet.
- **§17 Field/Batch Specialist** — Ratatosk: element NER, blackboard, propose-only.
- **§17.3 Ratatosk bootstrap flow** — wipe → ModelSummary → extract elements → Munin handoff via MCP.
- **§17.6 Agent identities** — `RataskAgent` (small/fast) vs `MuninAgent` (planning).
- **§18.4 Tool inventory** — `list_elements`, `list_relationships`, `list_stereotypes`, `propose_changeset`, `record_ratatosk_run`, query tools.
- **§18.5 Auth** — Bearer PAT at transport; never accept `user_id` in tool args; read-only token → `PermissionError` before write.
- **ChangeSet invariant** — all writes through Munin/ChangeSet; bootstrap ops use `source=ratatosk`.

---

## Baseline context map

Read these before any scenario implementation.

| File | Lines | Note |
|------|-------|------|
| `docs/features/user_journey.md` | 79–153 | Act 1 transcript: `building ModelSummary`, wipe rule, Munin handoff narrative |
| `docs/architecture/SAO.md` | §17.3, §18.4 | Bootstrap pipeline and MCP tool contracts |
| `ratatosk/cli.py` | 38–100 | `_build_llm()`, bootstrap command — no config module yet |
| `ratatosk/discovery/runner.py` | 51–120 | Django-free orchestration; log phrases still say `fetching existing model state` |
| `src/yggdrasil/ratatosk/agent.py` | 620–710 | In-process bootstrap/update + `McpHandoffPort` / `LocalOrmHandoffPort` |
| `src/yggdrasil/ratatosk/handoff.py` | 148–222 | Production handoff: `propose_changeset` + `record_ratatosk_run` |
| `src/yggdrasil/mcp/tools/propose.py` | 75–164 | Creates ChangeSet; does not invoke Munin for relationships |
| `src/yggdrasil/llm/adapters/ollama.py` | 59–90 | `complete()` raises `NotImplementedError` |
| `tests/integration/test_journey_bootstrap_then_update.py` | 48–117 | L1 journey — in-process MCP, not subprocess CLI |

---

## ChangeSet review mode (locked)

**Auto-apply above confidence 0.80** at `propose_changeset`. High-confidence element (and later relationship) ops land on the graph without manual `approve_changeset`. Below-threshold ops stay pending — Tier 2 `ACT-5-MCP-CHANGESET-01` covers that path.

Happy-path certification: bootstrap → auto-applied graph → MCP `list_elements` / `traverse` without approve step.

---

## Logging contract

All implementation must follow [.cursor/rules/do-informative-logging.mdc](../../../.cursor/rules/do-informative-logging.mdc):

- INFO at entry, decision branches, and exit for every public method touched.
- Each line answers **who / what / when / why** where relevant.
- Never log raw tokens or secrets.
- Verify listed log points appear in `logs/app.log` on happy and reject paths before marking a scenario done.

---

## Test contract

- pytest for unit/integration; behave for Gherkin where step defs exist.
- Integration: real DB, real services — no mocks (see `do-not-mock-in-integration-tests.mdc`).
- Red → green → refactor per scenario plan checkpoint command.

---

## AT vs subprocess split (document in each plan)

| Path | Used by | Proves |
|------|---------|--------|
| In-process `bootstrap_repository` + `LocalOrmHandoffPort` or `InProcessMcpToolClient` | DISC-01..16, journey L1 | Discovery logic, orphan invariant, blackboard |
| Subprocess `ratatosk bootstrap` + HTTP MCP | DISC-21, LLM-01..03, CLI-01, CLI-09 | Production CLI packaging, env config, remote MCP |

Both must eventually pass; they test different boundaries.
