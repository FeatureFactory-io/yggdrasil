# Activity: Define MCP Architecture

**Activity ID**: 61
**Order**: 20
**Phase**: Inception
**Dependencies**: Predecessor: Activity 44 (Define Integration & API Design, DTA-03)
**Condition**: Run only if the system exposes tools or resources via the Model Context Protocol. Skip if MCP is not in scope.

## Description

Define MCP Architecture

## Guidance

# Define MCP Architecture

## Objective

Decide the MCP integration case (A / B / hybrid), transport topology, tool inventory, and authentication pattern; document all decisions in SAO §18 — so that implementation follows a consistent, secure, and maintainable MCP layer.

**Reference:** `.cursor/playbooks/edda/artifacts/57-MCP_FastMCP_Reference_Architecture.md`

---

## When to Skip

Skip this activity (write "Not applicable" in SAO §18) if:
- The system has no MCP interface now and none is planned for the current iteration.

---

## Internal Process

1. **Read the reference architecture** — `.cursor/playbooks/edda/artifacts/57-MCP_FastMCP_Reference_Architecture.md` §0–§1 before answering any question below.
2. **Answer mission questions** — determine integration case and transport.
3. **Inventory tools** — decide which service callables become MCP tools.
4. **Design auth pattern** — process user, PAT per call, or both.
5. **Handle stdout hygiene** if stdio transport is selected.
6. **Record decisions** for SAO §18.

---

## Decisions to Make

### 1. Mission Assessment (answer all 7 questions)

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| Q1 | Who are the MCP clients? (AI IDE, Claude Desktop, custom script, cloud AI service) | | Determines transport and auth |
| Q2 | Should the MCP server embed business logic or delegate to the HTTP API? | | Case A vs. Case B vs. hybrid |
| Q3 | How is user identity established per tool call? (process user, PAT header, session cookie) | | Auth pattern |
| Q4 | Are any tools destructive? (write, delete, deploy, send) | | HITL and write-tool policy |
| Q5 | Is low-latency local IDE integration required? | | stdio transport |
| Q6 | Is multi-tenant or remote-client access required? | | HTTP+SSE transport |
| Q7 | Does stdout logging interference need to be prevented? | | Log routing for stdio |

### 2. Integration Case

Choose one:

- [ ] **Case A — Service Bridge**: MCP server calls internal service layer directly (same process or sidecar). Business logic lives in services; MCP is thin. Best for single-deployment systems.
- [ ] **Case B — API Facade**: MCP server calls the public HTTP API on behalf of the client. Tools mirror API endpoints. Best for multi-tenant / remote clients where the HTTP API is the canonical interface.
- [ ] **Hybrid**: Mix of A and B — some tools call services directly (internal ops), others call the API (user-facing ops).

Rationale: _____

### 3. Transport Topology

Define each deployment target:

| Target | Transport | Port / Path | Notes |
|--------|-----------|------------|-------|
| Local IDE (Cursor, Claude Desktop) | stdio | n/a | Requires stdout hygiene |
| Remote AI clients (cloud, custom) | HTTP+SSE | `:8001/mcp` | Auth header required |
| CI/CD pipeline | stdio or HTTP | | |

Topology decision: `[ ] stdio only` / `[ ] HTTP+SSE only` / `[ ] Both (dual server)`

### 4. Tool Inventory

List all tools. For each, determine:
- **Service method** — which function it wraps
- **Write?** — does it mutate state?
- **HITL?** — must a human approve before execution?

| Tool name | Service method | Write? | HITL? | Case |
|-----------|---------------|--------|-------|------|
| | | | | |
| | | | | |
| | | | | |

**Write-tool policy**: `[ ] Require explicit confirmation param` / `[ ] HITL prompt before execute` / `[ ] Audit log only`

### 5. Authentication Pattern

| Pattern | When to use |
|---------|------------|
| **Process user** — server runs as a single trusted identity | CI pipelines, local IDE stdio (trusted env) |
| **PAT per call** — client passes a Personal Access Token in the tool call; server validates | Remote clients, multi-tenant |
| **Session cookie** — HTTP transport with cookie-based session auth | Web-based MCP clients |

Selected pattern(s): _____

PAT injection point:
- `[ ] Tool argument (explicit)` — listed in tool schema; client passes every call
- `[ ] HTTP header (Bearer)` — transport-level; not in tool schema; avoids prompt injection

Rationale: _____

### 6. Stdout Hygiene (if stdio transport)

If stdio is selected, the MCP protocol uses stdout for its JSON wire format. Any non-JSON stdout breaks the client.

Action required:
- `[ ] Redirect all logging to stderr or a file (e.g. `logging.basicConfig(stream=sys.stderr)`)
- `[ ] Suppress third-party libraries that print to stdout (check Django startup, Celery, etc.)
- `[ ] Add a test that verifies no stdout noise on server boot

### 7. Case B: API Readiness Contract (if Case B or hybrid)

If tools call the HTTP API:

| Tool | HTTP endpoint | Method | Auth header |
|------|--------------|--------|-------------|
| | | | |

API readiness assertion: `[ ] Smoke test that all tool-target endpoints return 200 on health check`

---

## Scan Skills

Query Playbook Skills where `capability_domain` in:
- `MCP`
- `API_INTEGRATION`
- `AUTH`

Report coverage and gaps.

---

## Deliverables

- ✅ **Mission questions answered** (Q1–Q7 with rationale)
- ✅ **Integration case chosen** (A / B / hybrid) with rationale
- ✅ **Transport topology defined** (stdio / HTTP+SSE / both)
- ✅ **Tool inventory table** (tool name → service method → write? → HITL?)
- ✅ **Auth pattern defined** with injection point
- ✅ **Stdout hygiene** addressed (if stdio)
- ✅ **API readiness contract** defined (if Case B)
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO §18 (DTA-18)

## Agent

**Name**: Dr. Dobbs v2
**Description**: Cautious developer. Read the full MCP Reference Architecture before answering mission questions. Do not invent transport patterns — select from the catalog. Enforce the write-tool policy on every destructive tool.

## Skill

None

## Rules

See `../rules/` for full rule content.

## Notes

Exported via Mimir MCP tools.
