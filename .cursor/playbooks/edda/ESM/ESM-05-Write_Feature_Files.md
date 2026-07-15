# Activity: Write Feature Files

**Activity ID**: 39
**Order**: 5
**Phase**: Inception
**Dependencies**: Predecessor: Activity 38 (Create Dialogue Maps)

## Description

Write Feature Files

## Guidance

APPEND TO GUIDANCE:

---

## TFK Integration: Step Library Consumption

Before writing new step definitions in .feature files, **consult the TFK Step Library Catalog** (produced by TFK-03).

### Process

1. **Check existing steps**: Open the Step Library Catalog and search for steps matching your scenario needs. Steps are organized by domain: navigation, forms, tables, auth, assertions, dialogs.

2. **Assemble from library**: Compose your scenarios using existing step patterns. This is the primary mode of operation — think of it as assembling building blocks.

3. **If a step is missing**: Do NOT invent ad-hoc step definitions. Instead, invoke TFK-07 "Add Step and/or Fixture to Library" to create the new step following library conventions. TFK-07 will add it to the library and update the catalog.

4. **If a fixture is missing**: Similarly, check the Fixture Library Catalog (produced by TFK-04). If the needed test data preset doesn't exist, invoke TFK-07.

### Why This Matters

The step library is the shared vocabulary between ESM and TFK. When ESM writes `.feature` files using library steps, those scenarios become immediately executable by behave without additional step implementation work. Ad-hoc steps break this contract.

## Inputs (additional)

- **Step Library Catalog** (Document, Required) — produced by TFK-03 Build Step Library.
- **Fixture Library Catalog** (Document, Required) — produced by TFK-04 Build Fixture Library.

## Agent

None

## Skill

**Title**: Write Gherkin Feature Files
**Capability Domain**: BDD_AUTHORING
**Technology Stack**: Gherkin + Playwright + pytest-bdd

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
