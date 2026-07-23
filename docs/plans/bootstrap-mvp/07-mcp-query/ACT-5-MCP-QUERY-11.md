# ACT-5-MCP-QUERY-11 — list_packages returns metamodel package hierarchy

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** C4 seed packages
**Known gap:** INDEX.md — `list_packages` MCP tool missing

---

## Scenario (Gherkin)

```gherkin
@wip
When Priya calls list_packages model Yggdrasil
Then Technology and Application packages
And each entry includes parent package when nested
```

---

## Why this scenario matters

SAO A5.6 lists `list_packages` as scout drill-down tool — **spec requires, code missing**. Blocks Ratatosk scout parity and QUERY certification.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/server.py` | register | **Add** list_packages |
| `src/yggdrasil/graph/models.py` | Package | parent FK hierarchy |
| `docs/plans/RATATOSK-SPEC-REALIGNMENT-PLAN.md` | A5.7 | Impl gap callout |

---

## Do Not Do

Inherit SHARED-CONTRACT — read-only; no package CRUD via MCP in MVP.

---

## SAO.md Sections That Apply

- §18.4 list_packages (inventory)
- A5.6 scout allowed tools

---

## Current State Assessment

**Tool not implemented** — primary deliverable of this scenario.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_packages_c4_hierarchy` | integration | Technology, Application |
| `test_list_packages_parent_field` | integration | nested parent when child exists |
| `test_list_packages_tool_registered` | unit | MCP server tool list |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_packages` | entry | model_slug |
| `list_packages` | exit | package_count, root_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `list_packages` | MetamodelQueryService.list_packages | No |

---

## Implementation Steps

1. **Red:** test tool not in registry — fails.
2. **Green:** Service method query Package for model's metamodel.
3. **Green:** Register FastMCP tool with model param.
4. **Green:** Response includes parent slug or null.
5. **TFK07:** mcp_steps for list_packages @wip scenario.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_packages_c4_hierarchy -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "list_packages" with:` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-validate-api-contracts.mdc
- do-informative-logging.mdc
