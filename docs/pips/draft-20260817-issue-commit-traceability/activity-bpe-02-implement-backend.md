## Purpose
Implement backend services, models, and views following test-first development and small increments approach.

## Steps

### 1. Create Skeletons
Create all class and method skeletons with full docstrings following your language's documentation conventions.

The core principle: the developer who has no knowledge of the system can implement methods/properties etc. following only documentation in the skeleton.

- Create class and method/function stubs and document them
- Include full docstrings, return types, and sample return values
- Use appropriate placeholder (e.g., `NotImplementedError`, `TODO`, `panic!`, etc.)
- Do not skip type hints or documentation
- Add comments inside the methods pointing attention to the logic flow, exception handling, logging etc.

### 2. Write Behavior Tests Before Logic
Write unit tests before writing method logic using your test framework. Use real dependencies in integration scenarios - no mocking.

### 3. Implement Incrementally (behavior green)
Work method-by-method. Each method/property should be: implemented → behavior-tested → then log-story tested (step 4) → committed.

### 4. Log Story — Caplog in the Same Slice
For each footprint method covered by the plan's **Log Story Script**:

1. Write `test_*_log_story_happy` and/or `test_*_log_story_reject` (red)
2. Emit INFO logs that satisfy story beats (`entry → config → validation → processing → branch → exit → error`) per `do-informative-logging`
3. Make log-story tests green using skill *Pytest Log Story Assertions* (`tests/support/log_story.py` → `assert_log_story`) once TFK-02 has bootstrapped the helper — per `do-assert-log-story`
4. Never defer logging to a later “informative logging pass” slice

### 5. Commit After Each Step
Write → run → test (behavior + log story) → evaluate → fix. Commit using Angular-style commit messages. Behavior and log-story green in the same commit.

**Issue #N (when active):** footer `Refs #N` on every slice commit; immediately `gh issue comment N` with `` `{short-sha}` ``, slice summary, next slice. Do not start the next plan slice until both are done. See rule `do-github-issues`.

### 6. Backend Architecture
- **Services Layer**: Business logic shared between different interfaces (API, Web UI, CLI, etc.)
- **Repository Pattern**: Data access abstraction (can be swapped)
- **Views/Controllers**: Return appropriate responses for your framework
- **API Endpoints**: Follow RESTful or your framework's conventions
- **Context/State**: Always validate and document

### 7. Route Registration
Register new routes/endpoints with descriptive names. Follow your framework's conventions for URL/route structure.

### 8. Testing Views/Controllers
Use your framework's test client. Test responses, validate context/state, check templates/views used, test dynamic endpoints. Include caplog assertions for Log Story Script rows on those views.

### 9. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `BACKEND_FRAMEWORK` — Backend implementation patterns for your tech stack
- `TEST_FRAMEWORK` — Testing patterns and best practices
- `LOGGING_PATTERN` — Logging implementation for your language
- `LOG_STORY_TESTING` — Pytest Log Story Assertions / caplog helpers
- `DOCSTRING_FORMAT` — Documentation format for your language

Apply reference implementations and patterns from matched Skills.

## Rules

Before implementing, **read** each Rule below in this playbook (by slug), then **apply** it to every change in this activity's footprint. Do not rely on memory of the rule text; do not paraphrase the rule body into this activity.

Required:
- `do-skeletons-first`
- `do-test-first`
- `do-not-mock-in-integration-tests`
- `do-informative-logging`
- `do-assert-log-story`
- `do-import-on-module-level`
- `do-write-concise-methods`
- `do-docstring-format`
- `do-follow-commit-convention`
- `do-small-increments`
- `pytest`
- `do-github-issues`

Activity-specific (not a substitute for the rules above):
- Log-story tests (`*_log_story_*` / caplog) ship in the **same** red→green slice as behavior — no deferred logging pass.

## Success Criteria
- All skeletons created with full documentation
- Behavior tests written before implementation and passing
- Log Story Script rows proven by passing `*_log_story_*` caplog tests in the same commit as behavior
- No deferred logging slice in the plan
- Code committed with proper messages
- Every slice commit for issue #N referenced in a GitHub issue comment with SHA
- Routes/endpoints properly registered
- Services layer properly structured
