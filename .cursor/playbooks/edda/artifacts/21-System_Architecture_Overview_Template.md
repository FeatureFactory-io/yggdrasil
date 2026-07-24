# System Architecture Overview Template

**Artifact ID**: 21
**Type**: Document
**Required**: False

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
Reference: Playbook artifact AI Agent Reference Architecture — scenario index and capability table
-->

### Scenario selection

<!-- Read scenario cards in the AI Agent Reference Architecture before ticking -->

| SC-ID | Name | When (summary) | Selected? | Rationale |
|-------|------|----------------|-----------|-----------|
| SC-01 | Conversational planner | User chat → tools → optional background plan/worker | | |
| SC-02 | Field extractor / batch ingest | D0 pre-filter → D1 LLM canonicalize → propose writes; no chat loop | | |
| SC-03 | Compiled pipeline | Trigger → known step graph; selective LLM steps | | |
| SC-04 | Event-driven nudge | Domain event → proactive message/plan without user opening chat | | |
| SC-05 | Governed mutations | Mutations/deletes need human approval before execute | | |

### Capability checklist

<!-- Copy CAP rows from the reference artifact capability table for every CAP implemented -->

| CAP-ID | Name | Implement? | Project module path |
|--------|------|--------------|---------------------|
| CAP-001 | LLM Port protocol | | |
| CAP-004 | ScriptedLLM | | |
| | | | |

### Assembly template

- **Template**: {T-01 Planner | T-02 Field | T-03 Pipeline | T-00 Custom}
- **Custom CAP list** (if T-00): CAP-___ , CAP-___ , …

### Agent identities (CAP-121 / CAP-122)

| Identity | Role | Model tier | Allowed tools |
|----------|------|------------|---------------|
| | | planning / execution / field | |

### Agent Blackboard (if CAP-070 selected)

| Key | Role | Durability |
|-----|------|-----------|
| | | |

- Durability tier: {A — in-process | B — run-persistent}
- Max board size (chars): ______

### Plan & Steps (if CAP-050 selected)

- States: `pending → running → completed | failed | waiting_retry`
- Hybrid step flags in use: {is_critical, is_planning, is_variable_assessment, data-only}

### Integration proof (DoD gate)

<!-- Map PRF-SCxx-xx test IDs from the reference artifact integration proof table -->

| PRF ID | Scenario | Test file |
|--------|----------|-----------|
| PRF-SC02-01 | SC-02 thinking JSON | |
| PRF-SC02-02 | SC-02 parse fail loud | |
| PRF-SC02-03 | SC-02 D0 pre-filter | |
| PRF-SC02-04 | SC-02 D1 parse fail loud | |
| PRF-SC01-01 | SC-01 plan handoff | |
| PRF-SC01-02 | SC-01 429 retry | |
| PRF-SC01-03 | SC-01 blackboard retain | |
| PRF-SC05-01 | SC-05 HITL | |
| PRF-SC05-02 | SC-02+05 full rescan invariants | |

### SC-02 × SC-05 full rescan (if batch ingest replaces snapshot)

Complete when **both** SC-02 and SC-05 are selected:

- [ ] Rescan delete ops meet auto-apply confidence threshold (or rescan disables partial auto-apply)
- [ ] ChangeSet apply ordering: deletes → updates → adds when rescan flag is set
- [ ] PRF-SC05-02 mapped to integration test file

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
