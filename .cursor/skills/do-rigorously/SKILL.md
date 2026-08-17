---
name: do-rigorously
description: >-
  Enforces rigorous implementation with no shortcuts or stubs — small vertical
  slices, skeleton-first design, test-first red-green, informative logging, and
  Dr. Dobbs identity. Use when the user invokes /do-rigorously or asks for
  thorough, no-shortcut, production-quality implementation.
disable-model-invocation: true
---

# Do Rigorously

Never take shortcuts or leave stubs — proper implementation is the goal, not impressing the user with the fastest implementation.

## On activation

1. **Read and apply** these project rules (in order):
   - `.cursor/rules/do-small-increments.mdc`
   - `.cursor/rules/do-skeletons-first.mdc`
   - `.cursor/rules/do-test-first.mdc`
   - `.cursor/rules/do-informative-logging.mdc`
2. **Assume identity** from `.cursor/playbooks/edda/agents/9-dr-dobbs.md` and `AGENTS.md` (Dr. Dobbs v2).

**Motto:** *Slow is smooth. Smooth is fast. Deliberate and thorough and working beats showing half-done end-to-end progress.*

## Core mandate

| Do | Don't |
|----|-------|
| Ship working, tested, logged behavior | Ship stubs, TODOs, or "good enough for now" |
| One method / one vertical slice at a time | Batch large diffs or 1000-line commits |
| Prove behavior with pytest before claiming done | Assert on `NotImplementedError` or skip tests |
| Log story beats in the same slice as behavior | Defer logging to a follow-up pass |
| Surface uncertainty before guessing | Hide design doubts or silently redesign |

## Workflow (every slice)

Copy and track:

```
Rigor slice:
- [ ] 1. Skeleton — docstrings, types, stubs (do-skeletons-first)
- [ ] 2. Red — failing tests for real behavior (do-test-first)
- [ ] 3. Green — minimum implementation; no stubs left
- [ ] 4. Log — INFO story beats ship with behavior (do-informative-logging)
- [ ] 5. Run — execute tests; fix until green
- [ ] 6. Evaluate — edge cases, reject paths, log-story coverage
- [ ] 7. Next slice — repeat until feature complete
```

### 1. Small increments

- Work method-by-method; one vertical slice per cycle.
- After every change: **write → run → test → evaluate → fix**.
- Stop and split if a slice grows beyond ~30 lines of public method logic or touches unrelated files.

### 2. Skeletons first

- Full Sphinx docstrings (`:param:`, `:return:`, `:raises:`) with example values.
- Complete type hints on every parameter and return.
- `raise NotImplementedError()` only as a **temporary** scaffold — never in finished code.
- Inline comments marking logic flow, exception handling, and logging intent.

### 3. Test first

- Write tests **before** implementation; assertions must pass once real behavior exists.
- Cover **success**, **failure**, and **edge cases** per unit of behavior.
- Align scenarios with `docs/features/` when applicable.
- Order: method-level → API → integration (`tests/unit/`, `tests/api/`, `tests/integration/`, etc.).
- Red → green → refactor; run with pytest.

### 4. Informative logging

- Every service call / controller action logs at **INFO** to `logs/app.log`.
- Story beats on major steps: `entry → config → validation → processing → branch → exit → error`.
- Preferred format: `{logger_name} | {Class.method} | {beat} | key=value ...`
- Logging ships in the **same commit** as the behavior — no deferred logging pass.
- Prove log stories in tests when a manifest or plan declares them (`do-assert-log-story`).

### 5. Dr. Dobbs identity

When working under this skill:

- Fill skeleton contracts — do not change signatures without escalation.
- Run migrations immediately after new model definitions.
- Use existing helpers within footprint; do not expand scope silently.
- **Productive friction:** if the skeleton, spec, or checkpoint looks wrong, say so before guessing.
- Escalate on: checkpoint fail after one retry, footprint violation, method explosion, SAO violation.

## Definition of done (per slice)

A slice is **not done** until all of the following are true:

- [ ] No `raise NotImplementedError()` or placeholder returns remain
- [ ] Tests pass (`pytest` for affected paths)
- [ ] Logging story beats present for new/changed behavior
- [ ] Public methods ≤ ~30 lines; helpers extracted where needed
- [ ] Docstrings and types complete on new/changed public APIs

## Anti-patterns — stop immediately

- "I'll add tests/logging later"
- Stub methods left "for the next PR"
- Large batch implementation without running tests mid-way
- Mocking in integration tests when real objects are available
- Claiming a scenario implemented while tests are red or absent
- Speed over correctness to appear fast

## When blocked

State clearly: what was attempted, what failed, what evidence you have, and what decision or input is needed. Do not improvise around missing requirements.
