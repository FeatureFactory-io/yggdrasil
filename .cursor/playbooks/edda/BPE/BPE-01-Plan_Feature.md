# Activity: Plan Feature

**Activity ID**: 96
**Order**: 1
**Phase**: Construction
**Dependencies**: None

## Description

Plan Feature

## Guidance

## Purpose
Plan a new feature implementation by analyzing requirements, assessing codebase state, creating detailed implementation plan, and preparing for execution.

## Prerequisites
- Feature specification or idea for what needs to be built
- Access to codebase and documentation

## Steps

### Step 0: Reset and Prepare
Reset your task plan. If there was work in progress on another task, create a TODO.md file documenting what was being worked on, what was completed, what remains to be done, and any blockers or notes.

### Step 1: Understand Architecture
Read `docs/architecture/SAO.md` (if exists) to identify architectural patterns and principles relevant to this implementation. Use it to guide design decisions. **Note which section headings govern this feature — you will need these in Step 6.**

### Step 2: Understand User Journey
Check `docs/features/user_journey.md` (if exists) to understand what you're building and how it integrates with other parts of the system.

### Step 3: Analyze Feature Specification
Read the feature specification thoroughly. If none exists, propose creating one first.

**Follow BDD/Gherkin format:**
- One scenario = one user goal achievable in single session
- Each scenario should be 5-10 steps maximum
- Use concrete examples, not abstract descriptions
- Follow GIVEN-WHEN-THEN structure
- Scenarios must be independently executable
- If specification has >2 scenarios, work scenario-by-scenario
- If scenarios are >10 lines, suggest breaking them down
- Step phrases: either reuse an exact pattern from [`docs/features/CATALOG.md`](../../../docs/features/CATALOG.md) (and fixtures from [`tests/fixtures/CATALOG.md`](../../../tests/fixtures/CATALOG.md)), **or** explicitly design a new catalogued step/fixture for this occasion (invoke TFK-07 and update the catalog). Do not invent one-off Gherkin that never lands in the catalog.

### Step 4: Assess Codebase State
Systematically review existing codebase:

a) **Identify reusable components:**
   - List components/views/services/models that can be reused/extended/integrated
   - Verify implementations actually exist (not just stubs with `NotImplementedError`)
   - Ask user: integrate with existing or replace?

b) **Check test coverage:**
   - For any reusable components without tests, add test creation to the plan
   - Maintain test coverage as you extend functionality

c) **Build context map:**
   Identify 3–5 existing `file:line_range` locations that an implementor must read to orient correctly. For each, write one line:
   - What pattern to follow
   - What to extend
   - What NOT to touch

   Format:
   ```
   | methodology/services/workflow_service.py | 45–80 | Follow this exact pattern for the new service |
   | mcp_integration/tools.py | 120–145 | Append here, do NOT restructure existing tools |
   | tests/integration/test_workflow_crud.py | 1–40 | Follow fixture setup pattern |
   ```

   The context map is the primary orientation tool for any implementor (human or AI) starting with zero context. If you cannot identify 3 meaningful references, the codebase assessment in step (a) is incomplete.

d) **Detect MCP / Agent surface:**
   - Check SAO §18 — is MCP in scope for this feature?
     If yes: locate `mcp/server.py` (or equivalent). Verify `initialize_mcp()` exists and is called on startup. If missing: add initialization to the plan before any tool registration step.
   - Check SAO §17 — does this feature add or extend agent capabilities?
     If yes: locate `ToolExecutor` (see artifact 56 §4.3). Verify it is instantiated and injected into the agent loop. If missing: add ToolExecutor initialization to the plan before service wiring.
   - Record the findings as additional one-liners in the Context Map (Step 4c):
     ```
     | mcp/server.py | <line> | FastMCP singleton — register new tools here |
     | llm/executor.py | <line> | ToolExecutor — wire service callables here |
     ```
     Skip a row if that surface is not in scope for this feature.

### Step 5: Clarification Questions
Ask clarification questions scenario-by-scenario: UI/UX details, data validation rules, error handling expectations, integration points, performance requirements.

If >5 questions total, create `FEAT_X.Y.Z_Clarifications.md` with all questions for user to answer in batch.

Update feature file and plan based on answers.

### Step 6: Create Implementation Plan
Write a step-by-step, todo-style, highly atomic implementation plan. The plan must include the following mandatory sections in addition to the implementation steps:

**Mandatory Section A — Context Map** (from Step 4c):
```
## Context Map
| File | Lines | Note |
|------|-------|------|
| {file} | {lines} | {one-line note} |
```

**Mandatory Section B — Do-Not-Do List:**
Derived explicitly from the SAO.md sections identified in Step 1. State each constraint as a prohibition:
```
## Do Not Do
- Do NOT create a new Django app
- Do NOT add a manager/repository layer — services call ORM directly
- Do NOT modify existing service method signatures
- Do NOT add async
```
If SAO.md has no applicable constraints for this feature, write: "No SAO.md constraints apply — standard patterns only."

**Mandatory Section C — SAO.md Sections That Apply:**
```
## SAO.md Sections That Apply
- §Services Layer: shared by MCP and Web UI, no MCP-specific logic in services
- §MCP Access Rules: draft = full CRUD, released = read-only
```

**Mandatory Section D — Tests to Create** (prove what's working):
Every plan must name the tests that will prove the scenario done. Empty "write some tests" is not enough — each row must state what it asserts.
```
## Tests to Create
| Test | Level | Proves |
|------|-------|--------|
| `test_create_token_rejects_blank_name` | unit | blank name → ValueError, no row written |
| `test_token_list_view_owner_isolation` | integration | user B cannot see user A's tokens (no mocks) |
| `test_login_view_get_renders_form` | view | 200 + email/password/submit testids present |
```
Rules: [`../rules/do-test-first.mdc`](../rules/do-test-first.mdc) · [`../rules/do-not-mock-in-integration-tests.mdc`](../rules/do-not-mock-in-integration-tests.mdc) · [`../rules/do-fix-tests.mdc`](../rules/do-fix-tests.mdc) · [`../rules/pytest.mdc`](../rules/pytest.mdc)

**Mandatory Section E — Logs to Emit** (diagnose what's not):
Every plan must name the decision points that will be logged at INFO. Empty "add logging" is not enough — each row must answer who/what/when/why when read from `logs/app.log`.
```
## Logs to Emit
| Where | Trigger | Must include |
|-------|---------|--------------|
| `TokenService.create_token` entry | method called | user_id, name, scope |
| `TokenService.create_token` reject | blank name | reason=blank_name (no raw token) |
| `TokenCreateView.post` exit | success/fail | status_code, token_id or error class |
```
Rules: [`../rules/do-informative-logging.mdc`](../rules/do-informative-logging.mdc) · [`../rules/add-logging.mdc`](../rules/add-logging.mdc)

**Mandatory Section F — MCP Tools to Expose** (skip with "Not applicable" if MCP is not in scope):
Every new service method that an MCP client must call needs a row. Omit write tools without a write-tool policy decision.
```
## MCP Tools to Expose
| Tool name | Service method | Write? | HITL? | Auth injection |
|-----------|---------------|--------|-------|----------------|
| `create_foo` | `FooService.create` | Yes | No | server-side user_id |
```
Rules: artifact 57 §3.2 (tool schema + descriptor), §3.3 (auth injection — never accept `user_id` from args), §3.4 (write-tool policy)

**Implementation Steps** (following the mandatory sections):

*Initial Setup:*
- Create and checkout new branch: `feature/feature-name`
- Enable "Plan mode" for planning phase

*For Each Scenario (in order):*

1. **Backend Implementation:**
   - Design models and data structures
   - Register new models with `/admin` module
   - Create utility/helper functions
   - Implement services (business logic shared by MCP and Web UI)
   - Add repository methods for data access (only if SAO allows — default: services call ORM)
   - Create Django Views (returning HTML templates)
   - Design URL patterns
   - **Rules to apply:**
     - Skeletons before bodies → [`../rules/do-skeletons-first.mdc`](../rules/do-skeletons-first.mdc)
     - Public methods ≤ 20–30 lines → [`../rules/do-write-concise-methods.mdc`](../rules/do-write-concise-methods.mdc)
     - Sphinx docstrings with examples → [`../rules/do-docstring-format.mdc`](../rules/do-docstring-format.mdc)
     - INFO logs on entry / branches / exit → [`../rules/do-informative-logging.mdc`](../rules/do-informative-logging.mdc)

6. **MCP Tool Registration (if SAO §18 in scope and Mandatory Section F is populated):**
   - For each row in Section F: declare the tool in `mcp/tools/` (or the project's tool module) wrapping the service method.
   - Apply auth injection: inject `user_id` server-side — never accept it as a client-supplied argument.
   - Register the tool with the FastMCP server in `initialize_mcp()`.
   - Apply stdout hygiene if stdio transport is selected (see artifact 57 §6: redirect logging to stderr, suppress startup noise).
   - **Rules to apply:**
     - Artifact 57 §3–§4 (tool schema, auth, descriptors) — [`../artifacts/57-MCP_FastMCP_Reference_Architecture.md`](../artifacts/57-MCP_FastMCP_Reference_Architecture.md)

7. **ToolExecutor Wiring (if SAO §17 in scope):**
   - Register the service callable in `ToolExecutor` under the tool name expected by the agent loop.
   - Ensure the return envelope matches the stable format (dict with `result` key or equivalent).
   - Mark the tool as HITL if it is destructive — no immediate execute without approval.
   - **Rules to apply:**
     - Artifact 56 §4.3 (Tool Surface + ToolExecutor) — [`../artifacts/56-AI_Agent_Reference_Architecture.md`](../artifacts/56-AI_Agent_Reference_Architecture.md)

2. **Frontend Implementation:**
   - Design Django templates with semantic HTML
   - Implement HTMX interactions for dynamic behavior
   - Create template partials for reusable components
   - Add graph visualizations with Graphviz (if needed)
   - Implement form handling and validation
   - Add semantic `data-testid` attributes for all interactive elements
   - **Rules to apply:**
     - Stable `data-testid` on interactive elements → [`../rules/do-semantic-versioning-on-ui-elements.mdc`](../rules/do-semantic-versioning-on-ui-elements.mdc)
     - Visual pass via human eye / screenshot → [`../rules/do-look-via-human-eye.mdc`](../rules/do-look-via-human-eye.mdc)

3. **Testing — prove what's working:**
   Fill Mandatory Section D before coding. For each listed test:
   - Write the failing test first (red) → implement minimum to pass (green) → refactor
   - Unit: isolate pure logic / validators
   - Integration: real DB, real services, **no mocks**
   - View: status codes, templates, `data-testid` presence
   - **Rules to apply:**
     - [`../rules/do-test-first.mdc`](../rules/do-test-first.mdc)
     - [`../rules/do-not-mock-in-integration-tests.mdc`](../rules/do-not-mock-in-integration-tests.mdc)
     - [`../rules/do-fix-tests.mdc`](../rules/do-fix-tests.mdc)
     - [`../rules/pytest.mdc`](../rules/pytest.mdc)
     - Continuous run after each slice → [`../rules/do-continuous-testing.mdc`](../rules/do-continuous-testing.mdc)
   - **MCP tools** (if Mandatory Section F is populated): the Tests to Create table must include at least one T1 and one T2 row per new tool:
     - **T1 (FastMCP Client)** — `async with Client(transport=mcp) as c: await c.call_tool(...)` — proves schema, registration, async path.
     - **T2 (Direct service)** — call the service method directly with a real DB — proves service/ORM wiring.
     - **T3 (Process / subprocess JSON-RPC)** — required when stdio transport is selected — proves entrypoint cleanliness (no stdout noise).
     - Full recipes in artifact 57 §7 — [`../artifacts/57-MCP_FastMCP_Reference_Architecture.md`](../artifacts/57-MCP_FastMCP_Reference_Architecture.md)

4. **Observability — diagnose what's not:**
   Fill Mandatory Section E before coding. For each listed log point:
   - Emit INFO that answers who / what / when / why (never raw secrets/tokens)
   - Log decision branches (accept vs reject, redirect target class, ownership check)
   - After a failure: read `logs/app.log` before guessing
   - **Rules to apply:**
     - [`../rules/do-informative-logging.mdc`](../rules/do-informative-logging.mdc)
     - [`../rules/add-logging.mdc`](../rules/add-logging.mdc)

5. **Commit Strategy:**
   After every principal step commit with Angular convention message format.
   Rule: [`../rules/do-follow-commit-convention.mdc`](../rules/do-follow-commit-convention.mdc) · small increments → [`../rules/do-small-increments.mdc`](../rules/do-small-increments.mdc)

### Step 7: Confirm Rule References
Rule links are embedded in Implementation Steps (items 1–5) and Mandatory Sections D–E.
Before submitting the plan: verify every major step still cites the applicable rule path under `../rules/`. Do not invent rules — only link files that exist.

### Step 8: No Time Estimates
Do NOT add hours/days to the plan - it's for AI to execute.

### Step 9: Submit for Approval
Present the complete plan to user for review and approval. Create `FEATURECODE_IMPLEMENTATION_PLAN.md` in `docs/plans/` directory.

Do not proceed to implementation without explicit approval.

### Step 10: GitHub Issue Management
If project has GitHub integration, search for existing issue or create new one.

**The issue body must contain all five mandatory sections inline — do not link to the plan file.** An implementor starting with zero context must be able to orient and implement using only the issue body. Required inline content:

- Full `## Context Map` table
- Full `## Do Not Do` list
- Full `## SAO.md Sections That Apply` list
- Full `## Tests to Create` table (what each test proves)
- Full `## Logs to Emit` table (decision points + required context fields)
- Checkpoint command (single pytest command proving the scenario done)
- Complete implementation plan (full text, not a link)

Issue structure:
```
<!-- SCENARIO -->
id: {S_N}
checkpoint:
  command: "pytest tests/integration/test_{feature}.py -x"
  expected_exit_code: 0
sao_sections:
  - "§{Section Name}"
do_not_do:
  - "Do NOT ..."
<!-- /SCENARIO -->

## Context Map
{table from Step 6}

## Do Not Do
{list from Step 6}

## SAO.md Sections That Apply
{list from Step 6}

## Tests to Create
{table from Step 6 — Mandatory Section D}

## Logs to Emit
{table from Step 6 — Mandatory Section E}

## Implementation Plan
{full plan text}

## Acceptance Criteria
- [ ] `{checkpoint command}` passes
- [ ] No regressions: `pytest tests/ -x` passes
- [ ] Each row in Tests to Create has a passing test
- [ ] Each row in Logs to Emit appears in `logs/app.log` on the happy path (and reject path where listed)
```

Add labels: Feature/Scenario/Enhancement/Bug/Refactoring/Infra and easy/medium/hard.
Start name with the Scenario prefix when available.
Before creating issue — check if issue with this prefix already exists.

## Rules to Follow

### I. Test-First Development
Every function/method must begin with a test. Tests prove that your implementation works as intended. As long as tests are not passing, you cannot claim that the scenario/class/method is implemented.

- The plan's **Tests to Create** table is the contract: each row must become a real passing test
- Review current implementation you are about to start testing to learn methods, properties, fields etc. you can use
- If actual implementation contradicts docstring - ask user what takes precedence
- Review design documentation for guidance on how things shall be implemented
- Write unit tests before implementing logic (do not write tests for NotImplementedError)
- Look into feature files to identify relevant scenarios
- Tests must test main success, border conditions, expected errors, handling of unexpected errors
- Start with method-level tests, then go to API, then to integration
- For integration: use real objects, connections, and data - no mocking
- Make the test fail, then implement logic to pass it
- Use pytest for running tests
- All tests must be placed in the `tests/` directory structure: unit tests in tests/unit/, integration tests in tests/integration/, API tests in tests/api/, E2E tests in tests/e2e/, service tests in tests/services/
- Never place test files in the root directory of the repository

### I-bis. Observable by Default (Logging)
Tests prove green; logs explain red. You cannot claim a scenario is done if `logs/app.log` cannot answer who did what, with which data, and why a branch was taken.

- The plan's **Logs to Emit** table is the contract: each row must appear at INFO on the listed path
- Never log secrets (raw tokens, passwords, API keys)
- Follow [`../rules/do-informative-logging.mdc`](../rules/do-informative-logging.mdc) and [`../rules/add-logging.mdc`](../rules/add-logging.mdc)

### II. Small Increments
Work in method-by-method steps. Implement small vertical slices. After every change: write → run → test → evaluate → fix. No large PRs or 1000-line commits.

### III. Write Concise Methods
When designing new methods, ensure the top-level (public) method is concise—ideally 20–30 lines maximum. Move all supporting logic and details into well-named private (or inner/helper) methods. The top-level method should clearly express the main workflow, delegating specifics to lower-level helpers.

Each helper/private method should do one thing and have a clear, descriptive name. Avoid cramming complex logic into the top-level method; instead, encapsulate details in private helpers.

### IV. GitHub Issue Management
When creating an Issue, create a task for the person with very little knowledge of the domain. Create a very detailed to-do, giving the person very little space to misinterpret what needs to be done.

The issue must be self-sufficient: context map, do-not-do list, SAO sections, tests-to-create, logs-to-emit, and implementation plan all inline — not linked. A cold-start implementor should be able to begin without reading any other file first.

### V. Commit Convention
Follow Angular convention:
```
<type>(<scope>): <subject>
<BLANK LINE>
<body - what changed>
<BLANK LINE>
<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

## Success Criteria
- Feature specification exists and is clear
- All clarification questions answered
- Codebase assessment complete, including context map (3–5 file:line_range references)
- Implementation plan contains all five mandatory sections: Context Map, Do-Not-Do, SAO.md Sections, Tests to Create, Logs to Emit
- All tests are explicitly listed with what they prove (not vague "add tests")
- All log decision points are explicitly listed with required context fields (not vague "add logging")
- Plan reviewed and approved by user
- GitHub issue created/updated with all five mandatory sections inline (not linked)
- Plan document saved to `docs/plans/`
- If MCP tools added: Tests to Create table contains T1 + T2 rows for each new tool (plus T3 if stdio transport)

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **User Journey** (Document, Required) — produced by Define User Journey (#36).
- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).
- **Feature Files** (Document, Required) — produced by Write Feature Files (#39).
- **HTML Mockups** (Code, Optional) — produced by Create Mockups (#40).
- **System Architecture Overview Template** (Template, Required) — produced by Write SAO.md (#59).

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

- **Github Issues** (`do-github-issues`)
- **Plan Before Doing** (`do-plan-before-doing`)
- **Pull Frequently** (`do-pull-frequently`)

## Artifacts Produced

- **Implementation Plan Template** (Template) - Required

## Artifacts Consumed

- **User Journey** (Document) - Required
- **Screen Flow / Dialogue Map** (Diagram) - Required
- **Feature Files** (Document) - Required
- **HTML Mockups** (Code) - Optional
- **System Architecture Overview Template** (Template) - Required

## Notes

No additional notes.
