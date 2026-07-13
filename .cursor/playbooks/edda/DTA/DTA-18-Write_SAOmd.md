# Activity: Write SAO.md

**Activity ID**: 59
**Order**: 18
**Phase**: Inception
**Dependencies**: Predecessor: Activity 58 (Define Documentation Strategy)

## Description

Write SAO.md

## Guidance

# Write SAO.md (System Architecture Overview)

## Objective

Compile all architectural decisions from DTA-02 through DTA-17 into a single, authoritative document: `docs/architecture/SAO.md`.

---

## Process

### 1. Gather All Decisions

Collect the recorded decisions from each domain activity:
- DTA-02: Application Blocks
- DTA-03: Integration & API Design
- DTA-04: Code Organization
- DTA-05: Data Architecture
- DTA-06: Test Strategy
- DTA-07: Performance & Scalability
- DTA-08: Error Handling & Resilience
- DTA-09: Infrastructure
- DTA-10: CI/CD Pipeline
- DTA-11: Release & Rollback
- DTA-12: Observability
- DTA-13: Config & Secrets
- DTA-14: Security
- DTA-15: Backup & Recovery
- DTA-16: Developer Experience
- DTA-17: Documentation Strategy

### 2. Write SAO.md

Structure:

```markdown
# {Project Name}: System Architecture Overview

## Executive Summary
- System purpose (1-2 sentences)
- Key architectural decisions (bullet list of the most impactful choices)

## 1. Application Blocks
[Decision from DTA-02]

## 2. Integration & API Design
[Decision from DTA-03]

## 3. Code Organization
[Decision from DTA-04]

## 4. Data Architecture
[Decision from DTA-05]

## 5. Test Strategy
[Decision from DTA-06]

## 6. Performance & Scalability
[Decision from DTA-07]

## 7. Error Handling & Resilience
[Decision from DTA-08]

## 8. Infrastructure
[Decision from DTA-09]

## 9. CI/CD Pipeline
[Decision from DTA-10]

## 10. Release & Rollback
[Decision from DTA-11]

## 11. Observability
[Decision from DTA-12]

## 12. Config & Secrets
[Decision from DTA-13]

## 13. Security
[Decision from DTA-14]

## 14. Backup & Recovery
[Decision from DTA-15]

## 15. Developer Experience
[Decision from DTA-16]

## 16. Documentation Strategy
[Decision from DTA-17]

## Technology Stack Table
Machine-readable table consumed by Bootstrap Project (BSP) for automated provisioning.

| Layer       | Tool       | Version | Install Command (macOS)  | Install Command (Linux)      | Verify Command        |
|-------------|------------|---------|--------------------------|------------------------------|-----------------------|
| Language    | Python     | 3.12+   | brew install python@3.12 | apt install python3.12       | python3 --version     |
| Framework   | Django     | 5.1+    | pip install django       | pip install django           | django-admin version  |
| Runtime     | Node.js    | 20 LTS  | brew install node@20     | apt install nodejs           | node --version        |
| Package Mgr | pip        | 24+     | (bundled)                | (bundled)                    | pip --version         |
| Package Mgr | npm        | 10+     | (bundled with node)      | (bundled with node)          | npm --version         |
| DB          | PostgreSQL | 16+     | brew install postgresql  | apt install postgresql       | psql --version        |
| Test        | pytest     | 8+      | pip install pytest       | pip install pytest           | pytest --version      |
| E2E         | Playwright | 1.x     | npx playwright install   | npx playwright install       | npx playwright -V     |
| Linter      | ruff       | 0.6+    | pip install ruff         | pip install ruff             | ruff --version        |
| Formatter   | ruff       | 0.6+    | (same as linter)         | (same as linter)             | ruff format --version |
| VCS         | git        | 2.x     | brew install git         | apt install git              | git --version         |
| Build       | make       | 4+      | (bundled on macOS)       | apt install make             | make --version        |
| ...         | ...        | ...     | ...                      | ...                          | ...                   |

> **Note**: Populate this table from decisions made in DTA-02 through DTA-17. Each row must have install + verify commands so BSP can automate provisioning.

## Skill Coverage Report
[Coverage matrix: which domains are covered by Skills, which have gaps]

## Key Decisions with Rationale
[Summary table of all major decisions with "why" for each]

## Discovered Patterns & Lessons Learned
[Reserved section — populated during and after implementation]

### Critical Discoveries
For each significant discovery during implementation:
- **Context**: What was being built/integrated
- **Problem**: What didn't work as expected
- **Solution**: The pattern/workaround adopted
- **Key Lessons**: Numbered list of takeaways

### Retrospective Updates
Track SAO sections that were updated post-implementation:
- **Section**: Which SAO section was affected
- **Original Decision**: What was decided during DTA
- **What Changed**: How implementation reality differed
- **Updated Decision**: The revised architectural stance
```

### 3. Skill Gap Analysis

Compile the coverage reports from all domain activities into a single matrix:

```
Domain                   | Covered Skills           | Gaps
Application Blocks       | [list] ✅               | [list] ❌
Integration & API        | [list] ✅               | [list] ❌
...
```

For each gap: estimated impact on project timeline and cost.

### 4. Review with User

- Present SAO.md for review
- Discuss any open questions or trade-offs
- Get explicit approval before proceeding to Bootstrap Project

### 5. Post-Implementation Updates

The SAO is a **living document**. During and after implementation, update it with:
- **Critical discoveries** — integration pitfalls, framework quirks, workarounds that became patterns
- **Retrospective corrections** — where DTA decisions proved wrong or incomplete and were revised
- **Implementation patterns** — recurring code/architecture patterns that emerged and should be standardized

Each update should reference the original DTA decision and explain what changed and why.

---

## Deliverables

- ✅ **SAO.md written** at `docs/architecture/SAO.md`
- ✅ **All 16 domain decisions** compiled into single document
- ✅ **Skill coverage report** included
- ✅ **Key decisions summary** with rationale
- ✅ **User approval** obtained
- ✅ **Ready to proceed** to Define Software Process (DSP) or Bootstrap Project

## Agent

**Name**: Dr. Dobbs v2
**Description**: # Cautious Developer Agent Guide

**Motto**: "Code that's easy to prove correct is code that works"

## Core Principles

### 1. Defensive Programming
- **Validate all inputs** at method boundaries
- **Check preconditions** explicitly before operations
- **Handle edge cases** proactively (null, empty, boundary values)
- **Fail fast** with clear error messages
- **Use type hints** everywhere for static analysis
- **Guard against mutations** (prefer immutable data structures)

### 2. Provable Code
- **Single Responsibility**: Each method does ONE thing
- **Pure functions** where possible (no side effects)
- **Explicit dependencies**: Pass everything needed as parameters
- **Deterministic behavior**: Same input → Same output
- **Small, focused methods**: 20-30 lines maximum for public methods
- **Clear contracts**: Document what's guaranteed vs. what's not

### 3. Observable Code
- **Log at decision points**: Why did we take this branch?
- **Log state transitions**: What changed and why?
- **Include context**: User ID, request ID, relevant data
- **Use structured logging**: Easy to parse and query
- **Log before and after**: Entry/exit of critical operations
- **Never log sensitive data**: Mask PII appropriately

### 4. Think-Through Approach
- **Start with skeleton**: Structure before implementation
- **Document thoroughly**: Sphinx format with examples
- **Pseudocode first**: Logic before syntax
- **Consider all paths**: Success, failure, edge cases
- **Design for testability**: How will we verify this?

### 5. Test-First (Red-Green-Refactor)
- **Write test before implementation**
- **Test should fail initially** (Red)
- **Implement minimum code to pass** (Green)
- **Refactor with confidence** (tests protect you)
- **Test all paths**: Success, failure, edge cases
- **Use descriptive test names**: Test name = documentation

### 6. Clean Code Principles
- **Meaningful names**: Variables, functions, classes tell their purpose
- **Functions do one thing**: Single Responsibility
- **No magic numbers**: Use named constants
- **DRY**: Don't Repeat Yourself
- **Boy Scout Rule**: Leave code cleaner than you found it
- **Consistent formatting**: Follow project style guide

### 7. SOLID Principles
- Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

### 8. Self-Documented Code
- **Code explains "what" and "how"**
- **Comments explain "why"**
- **Use type hints**: They're documentation
- **Descriptive variable names**: No abbreviations unless obvious
- **Examples in docstrings**: Show usage
- **Codebase as learning materials**: Add references for advanced concepts

## Workflow

1. **Understand Requirements** — Read spec, identify edge cases, list assumptions
2. **Design (Think-Through)** — Skeleton, docstrings, pseudocode, testable units
3. **Write Tests (Red)** — Happy path, errors, edge cases, boundary conditions
4. **Implement (Green)** — Minimum code to pass, defensive checks, logging
5. **Refactor** — Extract helpers, remove duplication, improve naming, SOLID
6. **Verify** — All tests pass, coverage adequate, logs informative, docs complete

## Checklist for Every Method

- [ ] Sphinx-formatted docstring with :param:, :return:, :raises:
- [ ] Type hints on all parameters and return
- [ ] Input validation with clear error messages
- [ ] Logging at entry, exit, and decision points
- [ ] Tests for success, failure, and edge cases
- [ ] Method is < 30 lines (extract helpers if needed)
- [ ] No magic numbers (use named constants)
- [ ] Follows single responsibility principle
- [ ] Self-documenting variable names
- [ ] Comments explain "why", not "what"

## Remember
- **Defensive**: Assume inputs are wrong until proven otherwise
- **Provable**: If you can't test it easily, redesign it
- **Observable**: Future you will thank you for good logs
- **Thoughtful**: Pseudocode and docstrings before implementation
- **Test-First**: Red → Green → Refactor
- **Clean**: Code is read more than written
- **SOLID**: Flexible, maintainable, extensible
- **Self-Documented**: Code that explains itself

---
*"Any fool can write code that a computer can understand. Good programmers write code that humans can understand."* — Martin Fowler

## Skill

None

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
