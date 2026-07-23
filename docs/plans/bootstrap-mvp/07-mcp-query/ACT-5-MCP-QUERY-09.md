# ACT-5-MCP-QUERY-09 — list_stereotypes returns metamodel definitions

**Tier:** 2
**Wave:** W7
**Feature file:** `docs/features/act-5-mcp/mcp-query.feature`
**Package:** `07-mcp-query/`
**Depends on:** C4 seed, ACT-1-DISC-21 (CLI calls this during bootstrap)

---

## Scenario (Gherkin)

```gherkin
When Priya calls list_stereotypes model Yggdrasil
Then Container and Component in response
And each entry includes property_schema
```

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `src/yggdrasil/mcp/tools/query.py` | list_stereotypes | Used by Ratatosk CLI |
| `src/yggdrasil/graph/models.py` | Stereotype | property_schema JSON |

---

## Do Not Do

Inherit SHARED-CONTRACT — read-only catalog; not metamodel CRUD.

---

## SAO.md Sections That Apply

- §18.4 list_stereotypes
- A1.4 read-only catalog for CLI

---

## Current State Assessment

Tool likely exists from Act 0 agents work — verify property_schema in response.

---

## Tests to Create

| Test | Level | Proves |
|------|-------|--------|
| `test_list_stereotypes_c4_catalog` | integration | Container, Component |
| `test_list_stereotypes_property_schema` | integration | schema key on each row |

---

## Logs to Emit

| Where | Trigger | Must include |
|-------|---------|--------------|
| `list_stereotypes` | exit | model, stereotype_count |

---

## MCP Tools to Expose

| Tool | Service | Write? |
|------|---------|--------|
| `list_stereotypes` | MetamodelQueryService | No |

---

## Implementation Steps

1. Red test on property_schema presence.
2. Green serializer from Stereotype model.
3. Behave table assertions.

---

## Checkpoint

```bash
pytest src/yggdrasil/mcp/tests/test_query_tools.py::test_list_stereotypes_c4_catalog -x
```

---

## TFK-07 Steps Required

| Step phrase | File |
|-------------|------|
| `When Priya calls MCP tool "list_stereotypes" with:` | `mcp_steps.py` |

---

## Rules Applied

- do-test-first.mdc
- do-informative-logging.mdc
