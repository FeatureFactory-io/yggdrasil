# Activity: Establish E2E Infrastructure

**Activity ID**: 192
**Order**: 6
**Phase**: Elaboration
**Dependencies**: Predecessor: Activity 191 (Wire CICD Integration)

## Description

Establish E2E Infrastructure

## Guidance

# Establish E2E Infrastructure

## Objective

Set up the end-to-end test infrastructure that enables "day in life" user journey testing via Playwright-driven browser automation.

---

## Key Concepts

### E2E vs Acceptance Tests

| Aspect | Acceptance Test (AT) | E2E Test |
|--------|---------------------|----------|
| Focus | Proving ONE feature works | Fulfilling a GOAL using system means |
| Scope | Single .feature, single scenario | Multi-phase .feature, sequential |
| Speed | Fast (no browser) | Slow (real browser, screenshots) |
| When | Every CI run | Staging before release |

### Big Idea: Certify Any Environment

Using `--base-url=...` we can point Playwright at any place where the application runs:
- `--base-url=http://localhost:8000` — local development
- `--base-url=https://staging.example.com` — staging
- `--base-url=https://app.example.com` — production smoke test

Similarly `--db-uri=...` points where initial setup has to be loaded.

---

## Process

### 1. E2E Configuration

E2E tests use the `@e2e` tag which is excluded by default. They only run when explicitly invoked:
```bash
make test-e2e BASE_URL=https://staging.example.com DB_URI=postgres://...
```

### 2. E2E Feature Structure

Each E2E test is written as one long multi-phase .feature file running sequentially.

### 3. Screenshot on Every Step

environment.py captures a screenshot after every step for visual verification and debugging.

## Agent

None

## Skill

None

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
