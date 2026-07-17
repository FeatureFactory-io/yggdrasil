## Orient Summary — 2026-07-17

### Target
Acts: act-1-ratatosk, act-5-mcp, act-7-changeset, act-8-chat
Feature files:
- docs/features/act-1-ratatosk/ratatosk-bootstrap.feature (7 scenarios)
- docs/features/act-1-ratatosk/munin-briefing.feature (10 scenarios)
- docs/features/act-5-mcp/mcp-query.feature (10 scenarios)
- docs/features/act-5-mcp/mcp-write.feature (8 scenarios)
- docs/features/act-5-mcp/mcp-changeset.feature (6 scenarios)
- docs/features/act-7-changeset/changeset-list.feature (8 scenarios)
- docs/features/act-7-changeset/changeset-view.feature (12 scenarios)
- docs/features/act-8-chat/chat-munin.feature (10 scenarios)
Total: 71 scenarios

### Discovery — Scenarios Already Passing (Mockup AT)

Before writing a single line of code, 30 scenarios already pass under `behave --simple --wip`:

| File | Already passing | Notes |
|------|----------------|-------|
| changeset-list.feature | 8/8 | All mockup template + testids in place |
| changeset-view.feature | 10/12 | S11 needs rollback step def; S12 passes |
| munin-briefing.feature | 10/10 | All mockup template + testids in place |
| chat-munin.feature | 2/10 | S01, S02 pass; S03-10 need Munin step defs |

These 30 scenarios require only `@wip` graduation (removal of tag), no new production code.

### System Dependencies (PIN-03 Step 3 resolution)

| Dependency | Scenarios | Resolution |
|-----------|-----------|------------|
| Ollama local model | ACT-1-CLI-01 to 07, CHAT-MUNIN-1-03 to 10 | Option B (stub): ScriptedLLM for integration tests; real Ollama for E2E only. AT uses ScriptedLLM. Document in manifest as `ollama_service [STUBBED_FOR_AT]` |
| MCP step definitions (TFK-07) | All ACT-5-MCP-* scenarios | Option A: SINFRA-04 prerequisite scenario |
| CLI step definitions (TFK-07) | All ACT-1-CLI-* scenarios | Option A: SINFRA-05 prerequisite scenario |
| Munin step definitions (TFK-07) | CHAT-MUNIN-1-03 to 10 | Option A: SINFRA-06 prerequisite scenario |
| ChangeSet models | ACT-5-MCP-CHANGESET-*, rollback, write tools | Option A: SINFRA-01 prerequisite scenario |
| LLM Port (BaseLLM ABC) | All Munin + Ratatosk scenarios | Option A: SINFRA-02 prerequisite scenario |
| FastMCP server core | All ACT-5-MCP-* scenarios | Option A: SINFRA-03 prerequisite scenario |

### Scenarios in Scope (71 total)

**Group A — Graduation (already passing, remove @wip):**
S01: CHANGESET-LIST+FIND-1-01 … S08: CHANGESET-LIST+FIND-1-08
S09: CHANGESET-VIEW_CHANGESET-1-01 … S20: CHANGESET-VIEW_CHANGESET-1-12
S21: MUNIN-BRIEFING-1-01 … S30: MUNIN-BRIEFING-1-10
S31: CHAT-MUNIN-1-01, S32: CHAT-MUNIN-1-02

**Group B — ChangeSet service (no LLM):**
S33: CHANGESET-VIEW_CHANGESET-1-11 (rollback step def + service)
S34: ACT-5-MCP-CHANGESET-01 (approve_changeset all)
S35: ACT-5-MCP-CHANGESET-02 (approve_changeset item_ids)
S36: ACT-5-MCP-CHANGESET-03 (reject_changeset)

**Group C — MCP query tools (no LLM):**
S37: ACT-5-MCP-QUERY-01 … S46: ACT-5-MCP-QUERY-10

**Group D — Munin agent + write/changeset tools (ScriptedLLM for AT):**
S47: ACT-5-MCP-WRITE-01 (create_element → Munin → ChangeSet)
S48: ACT-5-MCP-WRITE-02 (create_element manual-review mode)
S49: ACT-5-MCP-WRITE-03 (update_element)
S50: ACT-5-MCP-WRITE-04 (delete_element blast-radius)
S51: ACT-5-MCP-WRITE-05 (create_relationship)
S52: ACT-5-MCP-WRITE-06 (update_relationships_batch)
S53: ACT-5-MCP-WRITE-07 (set_model_mode toggle)
S54: ACT-5-MCP-WRITE-08 (read-only token rejection)
S55: ACT-5-MCP-CHANGESET-04 (reject with reason → MuninRule)
S56: ACT-5-MCP-CHANGESET-05 (do_other → Munin re-plan)
S57: ACT-5-MCP-CHANGESET-06 (CI agent confidence workflow)

**Group E — Ratatosk CLI (ScriptedLLM for AT, subprocess step defs):**
S58: ACT-1-CLI-01 (bootstrap creates ChangeSet)
S59: ACT-1-CLI-02 (bootstrap with instructions)
S60: ACT-1-CLI-03 (delta buckets output)
S61: ACT-1-CLI-04 (Munin receives delta from Ratatosk)
S62: ACT-1-CLI-05 (auto-apply + queue below threshold)
S63: ACT-1-CLI-06 (missing token error)
S64: ACT-1-CLI-07 (C4 seeds automatically)

**Group F — Full Munin chat (ScriptedLLM for AT):**
S65: CHAT-MUNIN-1-03 (find and navigate)
S66: CHAT-MUNIN-1-04 (scope a view)
S67: CHAT-MUNIN-1-05 (propose via prefill link)
S68: CHAT-MUNIN-1-06 (timeline story)
S69: CHAT-MUNIN-1-07 (batch update via agentic loop)
S70: CHAT-MUNIN-1-08 (Markdown briefing with Mermaid)
S71: CHAT-MUNIN-1-09 (ground-truth only, no hallucination)
— CHAT-MUNIN-1-10 (ask_munin MCP tool) → overlaps Group C, uses same MCP server

### Scenarios Deferred
None — all 71 scenarios in scope.

### Velocity Trend
First iteration learning log. No prior velocity data.

### Dominant Drift
None — first iteration.

### Scope Validation

| Group | Risk | Flag |
|-------|------|------|
| A (graduation) | None — already passing | Green |
| B (ChangeSet service) | Low — simple Django service methods | Green |
| C (MCP query) | Medium — FastMCP async boundary requires sync_to_async discipline | Yellow |
| D (Munin write tools) | High — requires full Munin agent loop + Plan & Steps + Worker | Red |
| E (Ratatosk CLI) | High — separate PyPI package + subprocess + LLM | Red |
| F (Munin chat) | High — HTMX streaming + full agent loop | Red |

**scope_override:** confirmed — user has explicitly requested all 71 scenarios in this iteration.

### Infrastructure Prerequisites (SINFRA scenarios)

6 prerequisite scenarios created before the feature scenarios begin:
- SINFRA-01: ChangeSet app models (ChangeSet, ChangeSetItem, MuninRule + migration)
- SINFRA-02: LLM Port (BaseLLM ABC + ScriptedLLM + OllamaClient + AnthropicClient)
- SINFRA-03: FastMCP server core (mcp/server.py + mcp_server management command + stdio hygiene)
- SINFRA-04: MCP step definitions (docs/features/steps/mcp_steps.py)
- SINFRA-05: CLI step definitions (docs/features/steps/cli_steps.py)
- SINFRA-06: Munin agent step definitions (docs/features/steps/munin_steps.py)
