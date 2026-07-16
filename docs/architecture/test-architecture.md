# Test Architecture

**Artifact**: 48 (TFK-01 — Define Test Architecture)
**Authoritative detail**: [`docs/architecture/SAO.md § 5 — Test Strategy`](architecture/SAO.md#5-test-strategy)

---

## 1. Test Trophy Model

We follow the **Test Trophy**, not the traditional Pyramid.

```
E2E                      ← user completes a goal across multiple screens (staging only)
Acceptance / AT          ← one screen / one feature works as specified (every PR)
Integration (pytest)     ← real DB, real services, no mocks (every PR) ◄ main bet
Unit (pytest)            ← pure logic, custom querysets, LLM adapters (every PR)
CDK assertions           ← infra stacks, no AWS credentials (every infra/** PR)
```

**Why integration tests are the main bet:**
unit tests prove isolation, not behaviour; `model.save()` returning `OK` tells nothing about persistence.
Integration tests hit the sweet spot — real thing, no browser overhead, fast enough for CI.

---

## 2. Runner Mapping

| Layer | Runner | Notes |
|---|---|---|
| Unit | pytest + pytest-django | Thin — do not test framework behaviour or auto-generated views |
| Integration | pytest + Django test client | Real PostgreSQL, real services; **no mocks ever** |
| AT | behave + behave-django | `docs/features/` — spec and runner; Step Library in `docs/features/steps/` |
| E2E | behave + behave-django + Playwright | `tests/e2e/` — Playwright in steps; `@e2e` tag |
| CDK infra | `aws_cdk.assertions` | Synthesise in-memory; no AWS credentials required |

AT and E2E share the same `behave` / `behave-django` infrastructure.
The distinction is **scope and intent**, not tooling — see SAO.md for the full AT vs E2E comparison table.

---

## 3. Coverage Targets and Quality Gates

**Coverage is necessary but not sufficient.**
90 % coverage with useless tests is worse than 60 % with real integration tests.

| Layer | Target |
|---|---|
| Pure logic / custom querysets | 100 % unit test coverage |
| All CRUD + ChangeSet paths | 100 % covered by integration tests |
| Every `.feature` scenario | Must pass AT before merge |
| 5 user journeys | Must pass E2E on staging before `make swap` |

**Hard quality gates (enforced in CI and code review):**

- No mocks in integration or AT tests (`do-not-mock-in-integration-tests.mdc`)
- All pytest runs write to `tests.log` (`do-continuous-testing.mdc`)
- `data-testid` on every interactive control (`do-semantic-versioning-on-ui-elements.mdc`)
- BDD `.feature` file must exist in `docs/features/act-X/` before implementation begins
- `@wip` scenarios are excluded from CI (`behave.ini` `tags = ~@wip`); all other scenarios must pass AT before merge

---

## 4. Zero-Bug Policy

A bug is a failing integration or AT scenario — it is a **specification gap**, not an isolated defect.

1. When a bug is found, write a failing test that reproduces it **first**.
2. The test becomes the bug report (red).
3. Fix the code until the test passes (green).
4. The test stays in the suite permanently — regression coverage.

No bug is closed without a corresponding test. "Fixed but untested" is not fixed.

---

## 5. Zero-Length Feedback Workflow

The goal: code change → test result in the **shortest possible loop**.

```
edit file  →  pytest runs affected tests  →  result in <10 s
```

**Tooling:**
- `pytest-watch` (or `entr`) monitors file changes and re-runs the narrowest relevant test slice.
- Full suite (`make test`) runs on save for integration; unit-only for rapid iteration.
- `tests.log` always present — AI and human can diagnose without re-running.

**Rules:**
- Start `continuous_test_runner.py` (or `pytest-watch`) before any coding session.
- Monitor `tests.log` continuously; fix failures immediately — never accumulate a red suite.
- A clean `tests.log` is the definition of "ready to commit".

---

## Authoritative Reference

All detailed decisions, directory structure, fixture strategy, CI gate configuration, and the full AT vs E2E comparison table live in:

> **[`docs/architecture/SAO.md` — Section 5: Test Strategy](architecture/SAO.md#5-test-strategy)**

This document states principles. SAO.md is the source of truth.
