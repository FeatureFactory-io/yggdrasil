# Package 08 — MCP ChangeSet

Headless ChangeSet review tools — approve, reject, redirect via MCP.

**Wave:** W8
**Gate:** `pytest src/yggdrasil/mcp/tests/test_approve_changeset.py -x`

| File | Tier | Scenario |
|------|------|----------|
| [ACT-5-MCP-CHANGESET-01.md](ACT-5-MCP-CHANGESET-01.md) | 2 | Full approve pending ops |
| [ACT-5-MCP-CHANGESET-02.md](ACT-5-MCP-CHANGESET-02.md) | 4 DEFER | Partial approve item_ids |
| [ACT-5-MCP-CHANGESET-03.md](ACT-5-MCP-CHANGESET-03.md) | 4 DEFER | Reject all |
| [ACT-5-MCP-CHANGESET-04.md](ACT-5-MCP-CHANGESET-04.md) | 4 DEFER | Reject + LEARNED rule |
| [ACT-5-MCP-CHANGESET-05.md](ACT-5-MCP-CHANGESET-05.md) | 4 DEFER | do_other_changeset redirect |
| [ACT-5-MCP-CHANGESET-06.md](ACT-5-MCP-CHANGESET-06.md) | 4 DEFER | CI confidence workflow |

Bootstrap happy path uses auto-apply ≥0.80 — CHANGESET-01 covers manual path for sub-threshold ops left pending from CLI-05.
