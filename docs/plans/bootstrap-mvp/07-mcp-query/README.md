# Package 07 — MCP Query

Read-only MCP tools to browse bootstrapped graph from Cursor/Claude — post W6 certification.

**Wave:** W7
**Gate:** `pytest src/yggdrasil/mcp/tests/test_query_tools.py -x` (create suite if missing)

| File | Tier | Tool |
|------|------|------|
| [ACT-5-MCP-QUERY-01.md](ACT-5-MCP-QUERY-01.md) | 2 | `list_elements` paginated |
| [ACT-5-MCP-QUERY-02.md](ACT-5-MCP-QUERY-02.md) | 2 | `search` |
| [ACT-5-MCP-QUERY-03.md](ACT-5-MCP-QUERY-03.md) | 2 | `get_element` |
| [ACT-5-MCP-QUERY-04.md](ACT-5-MCP-QUERY-04.md) | 2 | `traverse` incoming |
| [ACT-5-MCP-QUERY-07.md](ACT-5-MCP-QUERY-07.md) | 2 | `list_changesets` |
| [ACT-5-MCP-QUERY-08.md](ACT-5-MCP-QUERY-08.md) | 2 | `get_changeset` |
| [ACT-5-MCP-QUERY-09.md](ACT-5-MCP-QUERY-09.md) | 2 | `list_stereotypes` |
| [ACT-5-MCP-QUERY-11.md](ACT-5-MCP-QUERY-11.md) | 2 | `list_packages` **impl gap** |
| [ACT-5-MCP-QUERY-05.md](ACT-5-MCP-QUERY-05.md) | 4 DEFER | stereotype filter |
| [ACT-5-MCP-QUERY-06.md](ACT-5-MCP-QUERY-06.md) | 4 DEFER | `as_of` historical |
| [ACT-5-MCP-QUERY-10.md](ACT-5-MCP-QUERY-10.md) | 4 DEFER | `list_ratatosk_runs` |

**Fixture dependency:** Bootstrapped `Yggdrasil` model with journey seed (6+ elements, relationships from CLI-04) for QUERY-01..04.

TFK-07: `docs/features/steps/mcp_steps.py` — see [TFK07-AT-STEPS](../00-foundation/TFK07-AT-STEPS.md).
