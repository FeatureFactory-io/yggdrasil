# Define AI Agent Architecture

**Condition:** Run only if the system has in-app LLM agents (agentic loops, plan/worker execution, or LLM calls inside the application). Skip and write "Not applicable" in SAO §17 if none of: in-app agentic loop, LLM calls initiated by the app, plan/worker execution.

**Reference:** Playbook artifact **AI Agent Reference Architecture** (latest released Edda version).

## Objective

Pick scenario(s), select capabilities (`CAP-xxx`), choose an assembly template, and record decisions in SAO §17.

## Process

1. **Fetch** the latest AI Agent Reference Architecture from the playbook.
2. Read **How to use** and **Scenario index** sections.
3. Pick primary **SC-xx** scenario(s); use the decision tree for secondary CAP additions.
4. Copy required + chosen optional **CAP-IDs** into SAO §17.
5. Confirm dependencies in the **Capability table** and **Module wiring** sections.
6. Note starting assembly template (T-01, T-02, T-03, or T-00 custom).
7. Name integration proof test IDs (`PRF-SCxx-xx`) as DoD gate.
8. Record decisions for SAO §17 via Write SAO.md (Activity 59).

## Decisions to Make

### 1. Scenario selection

Read the **Scenario cards** in the reference artifact before ticking. Record primary scenario(s) and rationale.

| SC-ID | Name | When (summary) | Selected? | Rationale |
|-------|------|----------------|-----------|-----------|
| SC-01 | Conversational planner | User chat → tools → optional background plan/worker | | |
| SC-02 | Field extractor / bootstrap | Batch input → LLM JSON → domain writes; no chat loop | | |
| SC-03 | Compiled pipeline | Trigger → known step graph; selective LLM steps | | |
| SC-04 | Event-driven nudge | Domain event → proactive message/plan without user opening chat | | |
| SC-05 | Governed mutations | Mutations/deletes need human approval before execute | | |

### 2. Capability checklist

From the reference artifact capability table — tick every CAP your project implements:

| CAP-ID | Name | Required for SC? | Implement? | Module path in project |
|--------|------|------------------|------------|------------------------|
| CAP-001 | LLM Port protocol | | | |
| … | (copy rows for each selected CAP) | | | |

Minimum: all **required** CAP-IDs from your selected SC-xx row.

### 3. Assembly template

- [ ] **T-01 Planner** (SC-01)
- [ ] **T-02 Field** (SC-02)
- [ ] **T-03 Pipeline** (SC-03)
- [ ] **T-00 Custom** — list CAP-IDs: _______________

### 4. Agent identities (CAP-121, CAP-122)

| Identity | Role | Model tier | Allowed tools |
|----------|------|------------|---------------|
| | | planning / execution / field | |

### 5. Agent Blackboard (if CAP-070 selected)

- Durability tier: A — in-process / B — run-persistent
- Schema keys: phase, hypothesis, current_plan, last_actions, next_intent
- Max board size (chars): ______

### 6. Integration proof (DoD gate)

Map reference artifact integration proof tests to project test files:

| PRF ID | Scenario | Test file | Selected? |
|--------|----------|-----------|-----------|
| PRF-SC02-01 | SC-02 thinking JSON | | |
| PRF-SC02-02 | SC-02 parse fail loud | | |
| PRF-SC01-01 | SC-01 plan handoff | | |
| PRF-SC01-02 | SC-01 429 retry | | |
| PRF-SC01-03 | SC-01 blackboard retain | | |
| PRF-SC05-01 | SC-05 HITL | | |

### 7. Scan Skills

Query Skills where `capability_domain` in: AI_AGENT, LLM_INTEGRATION, ASYNC_TASK. Report gaps.

## Deliverables

- Primary SC-xx scenario(s) chosen with rationale
- CAP-ID checklist complete for selected scenarios
- Assembly template (T-01 / T-02 / T-03 / T-00) named
- Agent identities + model tiers documented
- PRF test IDs mapped to project test files
- Skill coverage assessed
- Decision recorded for SAO §17 via Write SAO.md (Activity 59)
