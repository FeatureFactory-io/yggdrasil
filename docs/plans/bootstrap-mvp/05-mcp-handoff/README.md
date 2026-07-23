# Package 05 — MCP Handoff

Server-side MCP tools that Ratatosk CLI calls for bootstrap: `propose_changeset` and `record_ratatosk_run`.

**Wave:** W2 (before Ollama and in-process discovery)
**Gate:** `pytest src/yggdrasil/mcp/tests/test_propose_changeset.py tests/integration/mcp_harness/ -x`

| File | Tier | Proves |
|------|------|--------|
| [MCP-PROPOSE-CHANGESET.md](MCP-PROPOSE-CHANGESET.md) | 1 | ChangeSet create + auto-apply ≥0.80 |
| [MCP-RECORD-RATOSK-RUN.md](MCP-RECORD-RATOSK-RUN.md) | 1 | RataskRun blackboard persistence |

Blocks: ACT-1-DISC-21 (subprocess spy), ACT-1-CLI-01 (handoff at end of bootstrap).

Inherited: [SHARED-CONTRACT](../00-foundation/SHARED-CONTRACT.md) — no ORM writes from CLI, no bypass ChangeSet.
