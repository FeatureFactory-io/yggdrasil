# Activity: Define AI Agent Architecture

**Activity ID**: 60
**Order**: 19
**Phase**: Inception
**Dependencies**: Predecessor: Activity 44 (Define Integration & API Design)
**Condition**: Run only if the system has in-app LLM agents (agentic loops, plan/worker execution, or any LLM calls inside the application). Skip if the system is purely a data API or static site with no in-app agent.

## Description

Define AI Agent Architecture

## Guidance

# Define AI Agent Architecture

## Objective

Assess the AI agent mission, select modules from the AI Agent Reference Architecture, choose an assembly profile, and document all decisions in SAO §17 — so that implementation follows a coherent, testable agent stack.

**Reference:** `.cursor/playbooks/edda/artifacts/56-AI_Agent_Reference_Architecture.md`

---

## When to Skip

Skip this activity (write "Not applicable" in SAO §17) if all of the following are true:
- No in-app agentic loop (no ReAct/tool-calling loop inside the application)
- No LLM calls initiated by the application itself (only user-facing passthrough is fine)
- No plan/worker execution pattern

If MCP tools exist but the agent loop lives elsewhere (e.g. in the AI client), run DTA-20 for MCP and skip this activity.

---

## Internal Process

1. **Read the reference architecture** — `.cursor/playbooks/edda/artifacts/56-AI_Agent_Reference_Architecture.md` §0–§1 before answering any question below.
2. **Answer mission questions** — determine which modules are required.
3. **Select modules** — use the §1.3 selection matrix.
4. **Pick assembly profile** — §6, or compose a custom set and verify §2.2 dependency rules.
5. **Design module-specific details** — blackboard schema, step types, model tiers, etc.
6. **Name proof scenarios** — required for DoD gate.
7. **Record decisions** for SAO §17.

---

## Decisions to Make

### 1. Mission Assessment (answer all 10 questions)

Answer each question Yes / No / Partial and note the impact:

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| Q1 | Is the agent conversational, batch/pipeline, or both? | | Selects Agent Loop vs. compiled Plan |
| Q2 | Must work survive process crash / 429 mid-flight? | | Requires Plan & Steps + Worker + durable Blackboard |
| Q3 | Does the agent need tools against domain services? | | Requires Tool Surface |
| Q4 | Multi-turn reasoning with evolving intent inside one task? | | Requires Agent Blackboard |
| Q5 | Should the agent improve from user feedback / outcomes? | | Requires Learning |
| Q6 | Is there a large body of knowledge only partly relevant per task? | | Optional Knowledge Index |
| Q7 | Do users need live tokens / plan progress? | | Chat Streaming (SSE) and/or polling fallback |
| Q8 | Should domain events proactively message the user? | | Event Ingress |
| Q9 | Multiple personas or model tiers (planner vs. field)? | | Agent Factory / Identities |
| Q10 | Destructive actions need human approval? | | HITL on Tool Surface |

### 2. Module Selection

Using artifact 56 §1.3, mark each module:

| Module | Required / Optional / Skip | Rationale |
|--------|---------------------------|-----------|
| LLM Port | | |
| Prompt Stack | | |
| Tool Surface | | |
| Agent Loop | | |
| Plan & Steps | | |
| Worker | | |
| Agent Blackboard | | |
| Learning | | |
| Knowledge Index | | |
| Chat Streaming | | |
| Event Ingress | | |
| Agent Factory / Identities | | |

### 3. Assembly Profile

Choose one (or document a custom set with dependency check per artifact 56 §2.2):

- [ ] **Conversational planner** — chat → tools → optional plan → worker → notify
- [ ] **Compiled pipeline** — trigger → plan template → worker → domain artifact
- [ ] **Field / batch specialist** — batch input → tool/extract → optional blackboard → result
- [ ] **Custom** — document chosen subset + dependency validation

### 4. Agent Blackboard (if selected)

- Schema keys (max 5–7 keys, mission-tuned):

| Key | Role |
|-----|------|
| `phase` | |
| `hypothesis` | |
| `current_plan` | |
| `last_actions` | |
| `next_intent` | |

- Durability tier: `[ ] A — in-process` / `[ ] B — run-persistent (JSON column on plan/conversation)`
- Max board size (chars): ______
- Rationale: _____

### 5. Plan & Steps (if selected)

- State machine: `pending → running → completed | failed | waiting_retry` (standard) / custom:
- Hybrid step types in use:

| Flag | Used? | Rationale |
|------|-------|-----------|
| `is_critical` (abort on failure) | | |
| `is_planning` (LLM narrative step) | | |
| `is_variable_assessment` (LLM JSON metric) | | |
| Data step only (no LLM) | | |

- Step synthesis chain (prior LLM synthesis passed to subsequent steps): `[ ] Yes` / `[ ] No`
- Per-step model tier routing: `[ ] Yes` / `[ ] No`

### 6. Model Tiers & Identities

| Tier | Model | Used for |
|------|-------|---------|
| Planning (large) | | Narrative, planning steps, extended reasoning |
| Execution (medium) | | Assessment, tool-calling loops |
| Batch / field (small) | | Fast/cheap batch steps |

Agent identities (name + role + allowed tools):

| Identity | Role | Model tier | Allowed tools |
|----------|------|------------|---------------|
| | | | |

### 7. Agent Integration Proof (DoD Gate)

Name the integration test files/scenarios required by artifact 56 §7. These are blocking DoD gates — a slice is not done until these pass.

| Profile | Test file | Scenario |
|---------|-----------|---------|
| Happy path | | Message → tool → plan → worker → complete |
| Failed step | | Step marked failed; policy honored |
| 429 / rate limit | | Retry; completed steps not re-run |
| Bad LLM output | | Blackboard retained; no crash |
| Crash / resume | | Mid-plan restart; completed steps skipped |
| Destructive HITL | | Mutation not executed until approval (if HITL selected) |

### 8. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `AI_AGENT`
- `LLM_INTEGRATION`
- `ASYNC_TASK`

Report coverage and gaps.

---

## Deliverables

- ✅ **Mission questions answered** (Q1–Q10 with rationale)
- ✅ **Module set defined** (Required / Optional / Skip for each)
- ✅ **Assembly profile chosen** with dependency check
- ✅ **Agent Blackboard schema** documented (if selected)
- ✅ **Plan & Steps state machine + step types** documented (if selected)
- ✅ **Model tiers + agent identities** defined
- ✅ **Agent Integration Proof scenarios** named as DoD gate test files
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO §17 (DTA-18)

## Agent

**Name**: Dr. Dobbs v2
**Description**: Cautious developer. Read the full AI Agent Reference Architecture before answering mission questions. Do not invent modules — select from the catalog. Do not skip the proof scenarios — they are the DoD gate.

## Skill

None

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
