# Activity: Define Test Architecture

**Activity ID**: 187
**Order**: 1
**Phase**: Inception
**Dependencies**: None

## Description

Define Test Architecture

## Guidance

# Define Test Architecture

## Objective

Consume DTA-06 "Define Test Strategy" decisions and formalize the project's Test Trophy model, runner mapping, coverage policy, and zero-bug workflow.

---

## Decisions to Make

### 1. Test Trophy (not Pyramid)

Our model is the **Test Trophy** — integration tests are the main bet:

| Level | Weight | Runner | What it proves |
|-------|--------|--------|----------------|
| Unit | Thin | pytest | Custom queryset logic, pure utility functions, business logic methods — only where isolation adds value. Do NOT test default Model CRUD, auto-generated views, or framework behavior. |
| Integration | **Thick** | pytest | Feature works end-to-end with real DB, real services, real connections. **No mocking.** Think of them as acceptance tests minus the GUI. |
| Acceptance (AT) | Medium | behave-django | .feature scenarios executed against the running app. Steps assembled from the TAF Step Library. BDD-grade executable requirements. |
| E2E | Selective | behave + Playwright | Full user journey replaying "day in life" across multiple features. Sequential, slow, runs on staging before release. Takes screenshots for visual verification. |

### 2. Why Test Trophy over Pyramid

- Unit tests are limited: testing `model.save()` returns OK tells us nothing about whether data actually persisted
- Acceptance tests are expensive: real browser, slow, flaky
- Integration tests hit the sweet spot: real thing, no GUI overhead, fast enough for CI
- AT tests are just integration tests with BDD syntax — the .feature file IS the requirements document made executable

### 3. Runner Mapping

- **pytest**: everything up to and including integration tests
- **behave-django**: acceptance tests (.feature files with Given/When/Then)
- **behave + Playwright**: E2E tests (browser-driven, screenshots, LiveServerTestCase)

### 4. Coverage Policy

- Coverage metrics (coverage run and coverage report) are necessary but not sufficient
- **Coverage is meaningless without quality** — 90% coverage with useless tests is worse than 60% with real tests
- Quality gates: no mocking in integration tests, no testing framework behavior, no tests > 10 lines without extraction

## Agent

None

## Skill

**Title**: Test Trophy Architecture
**Capability Domain**: Test Strategy & Design
**Technology Stack**: testing-trophy, integration-testing

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
