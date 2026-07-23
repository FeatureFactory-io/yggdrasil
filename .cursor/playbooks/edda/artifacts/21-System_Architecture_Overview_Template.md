# System Architecture Overview Template

**Artifact ID**: 21
**Type**: Template
**Required**: True
**Produced By Activity ID**: 59
**Consumers**: 12

## Description

# {Project Name}: System Architecture Overview

## Executive Summary
- System purpose (1-2 sentences)
- Key architectural decisions (bullet list of the most impactful choices)

## 1. Application Blocks
<!-- Decision from DTA-02 -->
### Bounded Contexts / Domain Packages
- List domain packages with responsibilities

### Module Dependency Rules
- Dependency direction diagram or rules

### Foundational Architectural Pattern
- **Chosen**: {pattern}
- **Rationale**: Why this pattern over alternatives

### UI Architecture Patterns (if applicable)
- **Rendering model**: {server-rendered | SPA | hybrid} — rationale
- **Layout pattern**: {single-panel | multi-panel | wizard} — rationale
- **Component interaction model**: {full reload | partial updates | client-side state} — rationale
- **Visualization approach**: {server-generated | client-rendered | hybrid} — rationale

## 2. Integration & API Design
<!-- Decision from DTA-03 -->
### API Style
- **Chosen**: {style}
- **Rationale**: Why this style

### Versioning Strategy
- **Chosen**: {strategy}

### Contract Approach
- **Chosen**: {approach}

### External Integrations
- List 3rd party APIs, webhook patterns, retry policies

### Inter-Service Communication
- **Chosen**: {model}
- **Rationale**: Why this model

### Implementation Patterns
<!-- Populated during/after implementation -->
- Service-to-transport mapping:
- Sync/async boundary:
- Protocol-specific constraints:
- Shared service layer:
- Error propagation:

## 3. Code Organization
<!-- Decision from DTA-04 -->

## 4. Data Architecture
<!-- Decision from DTA-05 -->

## 5. Test Strategy
<!-- Decision from DTA-06 -->

## 6. Performance & Scalability
<!-- Decision from DTA-07 -->

## 7. Error Handling & Resilience
<!-- Decision from DTA-08 -->

## 8. Infrastructure
<!-- Decision from DTA-09 -->

## 9. CI/CD Pipeline
<!-- Decision from DTA-10 -->

## 10. Release & Rollback
<!-- Decision from DTA-11 -->

## 11. Observability
<!-- Decision from DTA-12 -->

## 12. Config & Secrets
<!-- Decision from DTA-13 -->

## 13. Security
<!-- Decision from DTA-14 -->

## 14. Backup & Recovery
<!-- Decision from DTA-15 -->

## 15. Developer Experience
<!-- Decision from DTA-16 -->

## 16. Documentation Strategy
<!-- Decision from DTA-17 -->

## 17. AI Agent Architecture
<!-- Decision from DTA-19 — omit this section if no in-app agent -->
<!--
Skip condition: write "Not applicable — no in-app LLM agent." and remove the subsections below
if DTA-19 was not run.
Reference: docs/architecture/artifacts/56-AI_Agent_Reference_Architecture.md
-->

### Mission Assessment

<!-- Answer Q1–Q10 from artifact 56 §1.1, or "Not applicable" -->
| # | Question | Answer | Impact |
|---|----------|--------|--------|
| Q1 | Conversational, batch/pipeline, or both? | | |
| Q2 | Must work survive process crash / 429 mid-flight? | | |
| Q3 | Does the agent need tools against domain services? | | |
| Q4 | Multi-turn reasoning with evolving intent inside one task? | | |
| Q5 | Should the agent improve from user feedback / outcomes? | | |
| Q6 | Large body of knowledge only partly relevant per task? | | |
| Q7 | Do users need live tokens / plan progress? | | |
| Q8 | Should domain events proactively message the user? | | |
| Q9 | Multiple personas or model tiers (planner vs. field)? | | |
| Q10 | Destructive actions need human approval? | | |
| Q11 | Does the agent parse structured JSON from LLM output? | | Requires thinking-aware normalization |

### Module Selection

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

### Assembly Profile

- **Profile**: {conversational planner | compiled pipeline | field/batch specialist | custom}
- **Dependency check**: _passed / see note_

### Agent Blackboard (if selected)

| Key | Role | Durability |
|-----|------|-----------|
| | | |

- Durability tier: {A — in-process | B — run-persistent}
- Max board size (chars): ______

### Plan & Steps State Machine (if selected)

- States: `pending → running → completed | failed | waiting_retry`
- Hybrid step types in use: {is_critical, is_planning, is_variable_assessment, data-only}
- Step synthesis chain: {Yes | No}
- Per-step model tier routing: {Yes | No}

### Model Tiers & Agent Identities

| Tier | Model | Used for |
|------|-------|---------|
| Planning (large) | | |
| Execution (medium) | | |
| Batch / field (small) | | |

| Identity | Role | Model tier | Allowed tools |
|----------|------|------------|---------------|
| | | | |

### Thinking Models (if Q11 yes)

<!-- Omit if no structured JSON extraction from LLM output -->
<!-- Reference: artifact 56 §4.1 — Thinking model response normalization -->

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Response contract | `LLMResponse.content` / `LLMResponse.thinking` | |
| Adapter normalization | {adapter module} | |
| Structured extract utility | {module path} | |
| Field-tier max_tokens | | Thinking headroom before JSON |
| Thinking log policy | DEBUG traces; INFO content/thinking char counts | |

### Agent Integration Proof (DoD Gate)

| Profile | Test file | Scenario |
|---------|-----------|---------|
| Happy path | | |
| Failed step | | |
| 429 / rate limit | | |
| Bad LLM output | | |
| Thinking-wrapped JSON | | Parse succeeds; no silent zero-op |
| Crash / resume | | |
| Destructive HITL | | |

## 18. MCP Architecture
<!-- Decision from DTA-20 — omit this section if no MCP interface -->
<!--
Skip condition: write "Not applicable — no MCP interface." and remove the subsections below
if DTA-20 was not run.
Reference: docs/architecture/artifacts/57-MCP_FastMCP_Reference_Architecture.md
-->

### Integration Case

- **Chosen**: {Case A — Service Bridge | Case B — API Facade | Hybrid}
- **Rationale**: _____

### Transport Topology

| Target | Transport | Port / Path | Notes |
|--------|-----------|------------|-------|
| Local IDE | stdio | n/a | |
| Remote AI clients | HTTP+SSE | | |

### Tool Inventory

| Tool name | Service method | Write? | HITL? | Case |
|-----------|---------------|--------|-------|------|
| | | | | |

- Write-tool policy: {Require explicit confirmation param | HITL prompt before execute | Audit log only}

### Auth Pattern

- **Selected**: {Process user | PAT per call | Session cookie | Mixed}
- **PAT injection point**: {Tool argument | HTTP header (Bearer)}
- **Rationale**: _____

### Stdout Hygiene (if stdio)

- Logging redirected to stderr / file: {Yes | N/A}
- Third-party stdout suppressed: {Yes | N/A}
- Boot noise test added: {Yes | N/A}

### API Readiness Contract (if Case B)

| Tool | HTTP endpoint | Method | Auth header |
|------|--------------|--------|-------------|
| | | | |

## Technology Stack Table

Machine-readable table consumed by Bootstrap Project (BSP) for automated provisioning.

| Layer | Tool | Version | Install Command (macOS) | Install Command (Linux) | Verify Command |
|-------|------|---------|-------------------------|-------------------------|----------------|
| ...   | ...  | ...     | ...                     | ...                     | ...            |

> **Note**: Each row must have install + verify commands so BSP can automate provisioning.

## Skill Coverage Report

| Domain | Covered Skills | Gaps |
|--------|---------------|------|
| Application Blocks | | |
| Integration & API | | |
| Code Organization | | |
| Data Architecture | | |
| Test Strategy | | |
| Performance & Scalability | | |
| Error Handling & Resilience | | |
| Infrastructure | | |
| CI/CD Pipeline | | |
| Release & Rollback | | |
| Observability | | |
| Config & Secrets | | |
| Security | | |
| Backup & Recovery | | |
| Developer Experience | | |
| Documentation Strategy | | |
| AI Agent Architecture | | |
| MCP Architecture | | |

## Key Decisions with Rationale

| # | Domain | Decision | Rationale |
|---|--------|----------|-----------|
| 1 | | | |

## Discovered Patterns & Lessons Learned
<!-- Reserved section — populated during and after implementation -->

### Critical Discoveries

<!-- For each significant discovery during implementation: -->
<!--
#### Discovery: {title}
- **Context**: What was being built/integrated
- **Problem**: What didn't work as expected
- **Solution**: The pattern/workaround adopted
- **Key Lessons**:
  1. ...
-->

### Retrospective Updates

<!-- Track SAO sections updated post-implementation: -->
<!--
| Section | Original Decision | What Changed | Updated Decision |
|---------|-------------------|--------------|------------------|
| | | | |
-->
