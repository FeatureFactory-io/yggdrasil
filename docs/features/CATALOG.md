# Step Library Catalog (TFK-03 / Artifact 49)

Authoritative reference for Gherkin step patterns used by ESM-05 feature specs and BPE-04
acceptance tests. See also: [`tests/fixtures/CATALOG.md`](../tests/fixtures/CATALOG.md).

**Rule (ESM-05):** search this catalog before writing any step phrase. If the pattern you need
is not here, invoke **TFK-07** — do not invent ad-hoc steps.

**Rule (AT honesty):** Acceptance tests MUST hit real app URLs (`/auth/…`, `/api/…`,
service entrypoints). `/mockups/` is DEBUG design reference only — never an AT target.
MCP ATs that call Python tool functions directly are T2 only; T1 (FastMCP Client) and
T3 (`manage.py mcp_server` stdio) live under `tests/integration/mcp_harness/`.

---

## How to Use (ESM-05)

1. Find your domain section below and pick the closest matching pattern.
2. Compose scenarios **only** from catalogued patterns.
3. Use exact mockup `data-testid` values from the [Mockup Testid Reference](#mockup-testid-reference).
4. If a step or fixture is missing → add a row to [Known Gaps](#known-gaps--tfk-07) and invoke TFK-07
   in BPE-04 rather than blocking spec authoring.

---

## AT vs E2E Runner Matrix

| Domain | AT runner | E2E runner |
|--------|-----------|-----------|
| Navigation | `docs/features/steps/navigation_steps.py` | `tests/e2e/steps/navigation_steps.py` |
| Auth | `docs/features/steps/auth_steps.py` (works) | `tests/e2e/steps/auth_steps.py` (**stub** — NotImplementedError) |
| Forms | `docs/features/steps/form_steps.py` | `tests/e2e/steps/form_steps.py` |
| Tables | `docs/features/steps/table_steps.py` | `tests/e2e/steps/table_steps.py` |
| Assertions | `docs/features/steps/assertion_steps.py` | `tests/e2e/steps/assertion_steps.py` |
| Dialogs | `docs/features/steps/dialog_steps.py` | `tests/e2e/steps/dialog_steps.py` |
| HTTP | `docs/features/steps/http_steps.py` | **AT only** |
| Common/Wait | `docs/features/steps/common_steps.py` | `tests/e2e/steps/common_steps.py` |

---

## Domain: Navigation

**File:** `navigation_steps.py` (AT + E2E, same patterns)

| Pattern | Runner | Preconditions | Example |
|---------|--------|---------------|---------|
| `Given the user is on the "{page_name}" page` | AT+E2E | `page_name` in PAGE_REGISTRY (BPE adds entries) | `Given the user is on the "landing" page` |
| `When the user navigates to the "{page_name}" page` | AT+E2E | Same | `When the user navigates to the "landing" page` |
| `Then the user should see the "{page_name}" page` | AT+E2E | Same | `Then the user should see the "landing" page` |

**AT implementation:** `reverse(url_name)` → `test_client.get(path)` → stores `context.response`.

**E2E implementation:** `context.page.goto(url)` via Playwright.

**PAGE_REGISTRY current entries:** `"landing"` → `web:index`, `"health"` → `health`.
Additional entries added by BPE-04 when new AT scenarios are added to `docs/features/`.

---

## Domain: Auth

**File:** `auth_steps.py`

| Pattern | Runner | Preconditions | Example |
|---------|--------|---------------|---------|
| `Given the user is logged in as "{role}"` | AT only | `role` ∈ `admin`, `architect`, `viewer` | Session setup for non-login screens |
| `Given a user exists with email "{email}" and password "{password}"` | AT only | Creates DB user, no session | Login POST scenarios |
| `Given the user is not authenticated` | AT+E2E | — | `Given the user is not authenticated` |

**AT implementation:** `force_login()` is for non-login screens only. Login itself must POST `/auth/login/`.

**E2E:** `the user is logged in as "{role}"` raises `NotImplementedError` until login page ships (BPE).
`the user is not authenticated` clears Playwright cookies.

**Seed users available** (from `seed.json` / `team_preset.json`):

| Role | Email | Password |
|------|-------|----------|
| admin | `admin@example.com` | `test-pass-only-1234` |
| architect | `priya@example.com` | `test-pass-only-1234` |
| viewer | `elena@example.com` | `test-pass-only-1234` |

---

## Domain: Forms

**File:** `form_steps.py` (AT + E2E, same patterns)

| Pattern | Runner | Notes |
|---------|--------|-------|
| `When the user enters "{value}" into "{field}"` | AT+E2E | AT: accumulates in `context.form_data`; E2E: fills via Playwright |
| `When the user selects "{option}" from "{dropdown}"` | AT+E2E | AT: accumulates; E2E: `select_option` |
| `When the user clicks "{button}"` | AT+E2E | AT: asserts `data-testid="{button}-btn"` exists; E2E: clicks it |
| `When the user submits the form` | AT+E2E | AT: POST accumulated form_data to current path; E2E: click submit |

**Testid conventions:**

| What you write | Testid looked up | Convention |
|----------------|------------------|-----------|
| `into "element-name"` | `element-name-input` | adds `-input` unless already ends in `-input` or `-select` |
| `from "element-stereotype"` | `element-stereotype-select` | adds `-select` unless already ends in `-select` |
| `clicks "create-element"` | `create-element-btn` | adds `-btn` unless already ends in `-btn` |
| `into "login-email"` | `login-email-input` (**MISMATCH**) | See Known Gaps #1 |

**Example:**
```gherkin
When the user enters "Payment API" into "element-name"
And the user selects "Container" from "element-stereotype"
And the user clicks "element-submit"
```

---

## Domain: Tables

**File:** `table_steps.py` (AT + E2E, same patterns)

| Pattern | Runner | Notes |
|---------|--------|-------|
| `Then the user sees table "{table_name}" with {n:d} rows` | AT+E2E | Looks for `data-testid="{table_name}-table"` + counts `*-row` items |
| `Then the table "{table_name}" should contain "{text}"` | AT+E2E | Text search inside table HTML |
| `When the user sorts table "{table_name}" by "{column}"` | AT+E2E | Checks/clicks `sort-{column}-btn` inside the table |

**Testid convention:** table container: `{table_name}-table`; row items: `{table_name}-row-{id}` pattern.

**Example:**
```gherkin
Then the user sees table "element-list" with 6 rows
And the table "element-list" should contain "Payment API"
```

---

## Domain: Assertions

**File:** `assertion_steps.py` (AT + E2E, same patterns)

| Pattern | Runner | Notes |
|---------|--------|-------|
| `Then the user should see "{text}"` | AT+E2E | AT: response body substring; E2E: visible text on page |
| `Then the user should not see "{text}"` | AT+E2E | Inverse |
| `Then the element "{test_id}" should be visible` | AT+E2E | AT: `data-testid="{test_id}"` in HTML; E2E: visible in Playwright |

**Example:**
```gherkin
Then the user should see "Payment API"
And the element "element-list-page" should be visible
```

---

## Domain: Dialogs

**File:** `dialog_steps.py` (AT + E2E, same patterns)

| Pattern | Runner | Notes |
|---------|--------|-------|
| `When the user confirms the dialog` | AT+E2E | Checks/clicks `dialog-confirm-btn` or `confirm-dialog-btn` |
| `When the user cancels the dialog` | AT+E2E | Checks/clicks `dialog-cancel-btn` or `cancel-dialog-btn` |
| `Then the dialog "{dialog_name}" should be visible` | AT+E2E | Checks `data-testid="{dialog_name}-dialog"` |

**Example:**
```gherkin
When the user clicks "delete-element"
Then the dialog "element-delete" should be visible
When the user confirms the dialog
```

**Note:** Mockup delete modals use `data-testid="confirm-delete-btn"` — covered by the step's fallback.

---

## Domain: HTTP (AT only)

**File:** `http_steps.py`

| Pattern | Runner | Notes |
|---------|--------|-------|
| `Given the application is running` | AT only | GET /health/ → 200 |
| `When I GET "{path}"` | AT only | Real app path, e.g. `"/auth/login/"` — never `/mockups/` |
| `When I POST "/auth/login/" with email "{email}" and password "{password}"` | AT only | Real LoginView POST |
| `Then the response status is {status:d}` | AT only | Asserts status code |
| `Then the response Location contains "{fragment}"` | AT only | Redirect Location substring |
| `Then the response redirects away from "{path}"` | AT only | 3xx and Location ≠ path |
| `Then the response body contains "{key}": "{value}"` | AT only | JSON body key-value check |

**Example:**
```gherkin
When I GET "/api/v1/elements/"
Then the response status is 200
```

---

## Domain: Common / Wait

**File:** `common_steps.py` (AT + E2E)

| Pattern | Runner | Notes |
|---------|--------|-------|
| `When the user waits {seconds:d} seconds` | AT+E2E | Rarely needed; prefer deterministic waits |

---

## Mockup Testid Reference

Quick-reference of `data-testid` values from mockup templates in
`src/yggdrasil/web/templates/mockups/`. Use these exact strings in `the element "{test_id}" should be visible`
assertions and in form step fields.

### AUTH-LOGIN-1 (`auth/login.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `auth-login-page` |
| Login form | `login-form` |
| Email input | `login-email` |
| Password input | `login-password` |
| Sign in button | `login-submit` |

### AUTH-TOKEN-1 (`auth/token.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `auth-token-page` |
| Generate token button | `generate-token-btn` |
| Token table row | `token-row-{id}` |
| Revoke token | `revoke-token-{id}` |
| Token name field (modal) | `token-name-input` |
| Token value (shown once) | `token-value` |
| New-token banner | `new-token-banner` |
| Create token submit | `create-token-submit` |
| Copy shell snippet | `snippet-copy-shell` |
| Copy Ratatosk CLI snippet | `snippet-copy-ratatosk` |
| Copy Ratatosk remote snippet | `snippet-copy-ratatosk-remote` |
| Copy MCP stdio snippet | `snippet-copy-mcp-stdio` |

### MUNIN-BRIEFING-1 (`munin/briefing.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `munin-briefing-page` |
| Review changeset | `review-changeset-btn` |
| Explore graph | `explore-graph-btn` |
| Next: review | `next-review-changeset` |
| Next: explore | `next-explore-graph` |
| Next: run again | `next-run-again` |
| C4 primer dismiss | `c4-primer-got-it` |

### VIEW-BROWSE-1 (`view/browse.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `view-browse-page` |
| Open Munin panel | `open-munin-btn` |
| Export button | `export-btn` |
| History button | `history-btn` |
| Saved views dropdown | `saved-views-dropdown` |
| Toggle filters | `filters-toggle` |
| Clear filters | `clear-filters-btn` |
| Package filter | `filter-package` |
| Stereotype filter | `filter-stereotype` |
| Health filter | `filter-health` |
| Time travel date | `filter-as-of` |
| Apply filters | `apply-filters-btn` |
| Table toggle | `toggle-table` |
| Graph toggle | `toggle-graph` |
| Results container | `results-container` |
| Graph Cytoscape container | `graph-cy-container` |
| Element row | `element-row-{id}` |
| View element link | `view-element-{id}` |

### EXPORT-BRIEFING-1 (`view/export.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `export-briefing-page` |
| Mermaid annotate toggle | `munin-annotate-mermaid` |
| Export Mermaid | `export-mermaid-btn` |
| Deck annotate toggle | `munin-annotate-deck` |
| Export slide deck | `export-deck-btn` |
| Export JSON | `export-json-btn` |

### VIEW-HISTORY-1 (`view/history.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `view-history-page` |
| Snapshot A date | `snapshot-a` |
| Snapshot B date | `snapshot-b` |
| Compare button | `compare-btn` |
| Timeline item | `timeline-item-{id}` |
| Open snapshot A | `open-snapshot-a` |
| Open snapshot B | `open-snapshot-b` |

### ELEMENT-LIST+FIND-1 (`element/list.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `element-list-page` |
| Create element | `create-element-btn` |
| Search input | `element-search` |
| Filter stereotype | `filter-stereotype` |
| Filter package | `filter-package` |
| Filter source | `filter-source` |
| Element row | `element-row-{id}` |
| View element | `view-el-{id}` |
| Edit element | `edit-el-{id}` |
| Delete element trigger | `delete-el-{id}` |
| Delete modal | `element-delete-modal` |
| Confirm delete | `confirm-delete-btn` |

### ELEMENT-CREATE_ELEMENT-1 (`element/create.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `element-create-page` |
| Create form | `element-create-form` |
| Name input | `element-name-input` |
| Stereotype select | `element-stereotype-select` |
| Package select | `element-package-select` |
| Owner input | `element-owner-input` |
| Add property | `add-property-btn` |
| Add relationship | `add-relationship-btn` |
| Diagram C1 | `diagram-C1` |
| Submit | `element-submit-btn` |

### ELEMENT-VIEW_ELEMENT-1 (`element/view.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `element-view-page` |
| Delete trigger | `delete-element-btn` |
| Edit button | `edit-element-btn` |
| Delete modal | `element-delete-modal` |
| Blast radius panel | `blast-radius-panel` |
| Delete form | `element-delete-form` |
| Confirm delete | `confirm-delete-btn` |

### ELEMENT-EDIT_ELEMENT-1 (`element/edit.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `element-edit-page` |
| Edit form | `element-edit-form` |
| Name input | `element-name-input` |
| Stereotype select | `element-stereotype-select` |
| Package select | `element-package-select` |
| Owner input | `element-owner-input` |
| Save button | `element-save-btn` |

### RELATIONSHIP-LIST+FIND-1 (`relationship/list.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `relationship-list-page` |
| Create relationship | `create-relationship-btn` |
| Search input | `relationship-search` |
| Filter edge stereotype | `filter-edge-stereotype` |
| Filter source | `filter-rel-source` |
| Relationship row | `relationship-row-{id}` |
| View | `view-rel-{id}` |
| Edit | `edit-rel-{id}` |
| Delete trigger | `delete-rel-{id}` |
| Delete modal | `relationship-delete-modal` |
| Confirm delete | `confirm-delete-btn` |

### RELATIONSHIP-CREATE_RELATIONSHIP-1 (`relationship/create.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `relationship-create-page` |
| Create form | `relationship-create-form` |
| From element | `from-element-input` |
| Edge stereotype | `edge-stereotype-select` |
| To element | `to-element-input` |
| Submit | `relationship-submit-btn` |

### RELATIONSHIP-VIEW_RELATIONSHIP-1 (`relationship/view.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `relationship-view-page` |
| Delete trigger | `delete-relationship-btn` |
| Edit button | `edit-relationship-btn` |
| Delete modal | `relationship-delete-modal` |
| Delete form | `relationship-delete-form` |
| Confirm delete | `confirm-delete-btn` |

### RELATIONSHIP-EDIT_RELATIONSHIP-1 (`relationship/edit.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `relationship-edit-page` |
| Edit form | `relationship-edit-form` |
| From element | `from-element-input` |
| Edge stereotype | `edge-stereotype-select` |
| To element | `to-element-input` |
| Save button | `relationship-save-btn` |

### CHANGESET-LIST+FIND-1 (`changeset/list.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `changeset-list-page` |
| Filter status | `filter-status` |
| Filter source | `filter-source` |
| Changeset row | `changeset-row-{id}` |
| Review link | `review-changeset-{id}` |

### CHANGESET-VIEW_CHANGESET-1 (`changeset/view.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `changeset-view-page` |
| Accept high-confidence | `accept-high-confidence-btn` |
| Reject all | `reject-all-btn` |
| Accept all | `accept-all-btn` |
| Rollback | `rollback-btn` |
| Operation row | `op-row-{id}` |
| Accept op | `accept-op-{id}` |
| Reject op | `reject-op-{id}` |
| Do Other trigger | `do-other-op-{id}` |
| Do Other input | `do-other-input-{id}` |
| Do Other submit | `do-other-submit-{id}` |

### RATATOSK_RUN-LIST+FIND-1 (`ratatosk_run/list.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `ratatosk-run-list-page` |
| Run row | `run-row-{id}` |
| View run | `view-run-{id}` |

### RATATOSK_RUN-VIEW_RATATOSK_RUN-1 (`ratatosk_run/view.html`)

| Purpose | `data-testid` |
|---------|---------------|
| Page container | `ratatosk-run-view-page` |
| View changeset link | `view-changeset-btn` |

### Global nav (`base.html`)

| Purpose | `data-testid` |
|---------|---------------|
| View Browser nav link | `nav-view-browser` |
| Elements nav link | `nav-elements` |
| Relationships nav link | `nav-relationships` |
| Changesets nav link | `nav-changesets` |
| Runs nav link | `nav-runs` |
| Settings nav link | `nav-settings` |
| User menu toggle | `user-menu` |
| Munin chat input | `munin-input` |
| Munin send button | `munin-send` |

---

## Canonical Test Data (from `mockups/views.py` + `seed.json`)

### Users

| Role | Email | Password |
|------|-------|----------|
| admin | `admin@example.com` | `test-pass-only-1234` |
| architect | `priya@example.com` | `test-pass-only-1234` |
| viewer | `elena@example.com` | `test-pass-only-1234` |

### Elements (MOCK_ELEMENTS, 6 total)

| id | Name | Stereotype | Package | Owner |
|----|------|-----------|---------|-------|
| 1 | Payment API | Container | Technology | payments-team |
| 2 | Notification Service | Container | Technology | platform-team |
| 3 | Order Domain | Component | Application | fulfillment-team |
| 4 | Fulfillment Worker | Component | Application | fulfillment-team |
| 5 | PostgreSQL | System | Technology | platform-team |
| 6 | Mobile App | System | Context | mobile-team |

### Relationships (MOCK_RELATIONSHIPS, 6 total)

| id | From | Edge | To |
|----|------|------|----|
| 1 | Mobile App | calls | Payment API |
| 2 | Payment API | depends_on | PostgreSQL |
| 3 | Payment API | calls | Notification Service |
| 4 | Order Domain | depends_on | Payment API |
| 5 | Fulfillment Worker | reads_from | PostgreSQL |
| 6 | Order Domain | serves | Fulfillment Worker |

### ChangeSets (MOCK_CHANGESETS, 3 total)

| id | Run | Source | Status | Operations |
|----|-----|--------|--------|-----------|
| 1 | run-003 | ratatosk | pending | 6 |
| 2 | run-002 | human | applied | 2 |
| 3 | run-001 | ratatosk | applied | 21 |

### Ratatosk Runs (MOCK_RUNS, 3 total)

| id | Trigger | Status | Duration |
|----|---------|--------|---------|
| 3 | `ratatosk bootstrap ./repo --model Yggdrasil` | complete | 2m 14s |
| 2 | manual GUI create | complete | 0m 08s |
| 1 | `ratatosk bootstrap ./repo --model Yggdrasil --metamodel=c4` | complete | 4m 31s |

### Tokens (MOCK_TOKENS, 2 total)

| id | Name | Scope |
|----|------|-------|
| 1 | laptop-ratatosk | read-write |
| 2 | cursor-mcp | read-only |

### Form option lists

Owned by Metamodel `c4` (Django admin / `ensure_c4_metamodel()`), not by each Model:

- **Element stereotypes:** System, Container, Component, Person, External
- **Packages:** Context, Technology, Application, Code
- **Edge stereotypes:** calls, depends_on, uses

### Metamodel AT steps (CLI)

| Step | Notes |
|------|-------|
| `Given the Metamodel "{slug}" exists with C4 stereotypes and packages` | Seeds catalog via `ensure_c4_metamodel()` when slug=`c4` |
| `Then the model's metamodel is "{slug}"` | Asserts immutable Model→Metamodel binding |
| `Then the model's metamodel contains packages from:` | Packages live on Metamodel |

### Discovery / ChangeSet invariant assertions

| Phrase / step | Notes |
|---------------|-------|
| `Then the exit code is 0` / `is not 0` | CLI subprocess exit |
| `And the output contains "{phrase}"` | Stable CLI log phrases (`token`, `MCP`, `nothing to scan`, `no architecture changes detected`, `building ModelSummary`, `wiping N elements`) |
| `And the output does not contain "{phrase}"` | Negative CLI assertions (`unchanged:`, `wiping` on update) |
| `And a ChangeSet with source "ratatosk" exists` | Handoff went through Munin pipeline |
| `And every new Element is referenced by an operation on that ChangeSet` | DISC-06 / CICD-13 — no orphan Elements |
| `And there are no orphan Elements without a ChangeSetItem` | Same invariant |
| `And the run blackboard contains step "{name}"` | Blackboard steps: `tree`, `project_map`, `extract`, `cleanup`, `handoff`, `scout_plan`, `metamodel_guidance` |
| `And the run blackboard contains key "{key}"` | Scout keys: `evidence_plan`, `tool_calls`, `model_summary_chars`, `sources` |
| `And the run blackboard has input_mode "stdin"` / `stdin kind "prose"` | Act 6 prose path |
| `When Marcus pipes the stdin fixture "{name}" into ratatosk update with repo "./repo"` | Update with local file reads (@wip) |
| `When Marcus pipes commit message stdin into ratatosk update with repo "./repo":` | Commit-log scout trigger (@wip) |
| `And an MCP tool call to "{tool}" was recorded on the blackboard` | Scout MCP drill-down (@wip) |
| `And the delta buckets contain bucket "{bucket}" with count at least {n}` | Bootstrap/update bucket min counts (DISC-03, CICD-15) |
| `When Priya runs ratatosk bootstrap against "{name}" with exclude "{patterns}"` | DISC-17 operator scope control |
| `When Priya runs ratatosk bootstrap against "{name}" with instructions:` | DISC-18 operator LLM steering |
| `Then the run blackboard tree does not include "{path}"` | DISC-17 excluded paths absent from tree |
| `Given Ratatosk has produced bootstrap buckets:` | CLI-04 Munin handoff fixture |
| `Then Munin produces ChangeSet with at least {n:d} planned operations` | CLI-04 relationship planning |
| `And the output contains wipe no-op for empty graph` | CLI-08: `wipe no-op for empty graph` |
| `Then bootstrap candidates include all manifest elements:` | DISC-01 / DISC-17 / DISC-18 manifest table |
| `Then bootstrap candidates do not include element "{name}"` | DISC-18 negative manifest assertion |
| `Given the environment variable "{name}" is set to "{value}"` | Bootstrap env (CFG-*, CLI-09) (@wip TFK-07) |
| `When Priya runs ratatosk bootstrap against fixture "{name}" via subprocess` | DISC-21 / LLM-* production CLI path (@wip TFK-07) |
| `Then MCP tool "{tool}" was called during bootstrap` | DISC-21 MCP handoff chain (@wip TFK-07) |
| `Given Ollama is reachable at "{url}"` | LLM-01 (@wip TFK-07) |
| `Given Ollama model "{model}" is not available` | LLM-02 (@wip TFK-07) |
| `Then the discovery LLM was invoked at least {n:d} times` | DISC-05 / LLM-01 |
| `When Ratatosk loads configuration for bootstrap` | CFG-06..09 (@wip TFK-07) |
| `Then the effective config key "{key}" is {value}` | CFG-* (@wip TFK-07) |
| `When Priya runs ratatosk bootstrap with flag "{flag}"` | CFG-02 (@wip TFK-07) |
| `Given a repo config file "ratatosk.yaml" with model_summary_token_budget {n:d}` | CFG-02 (@wip TFK-07) |
| `Given a repo config file "{path}" with llm_provider "{value}"` | CFG-12, CFG-13 (@wip TFK-07) |
| `Given a repo config file "{path}" with base_model "{value}"` | CFG-12 (@wip TFK-07) |
| `When Ratatosk loads configuration for bootstrap with repo "{path}"` | CFG-12, CFG-13 (@wip TFK-07) |
| `Then the effective config key "resolved_model" is "{value}"` | CFG-11, CFG-12 (@wip TFK-07) |
| `Then the effective config key "resolved_model" contains "{substring}"` | CFG-11 (@wip TFK-07) |
| `Given the environment variable "ANTHROPIC_API_KEY" is set` | LLM-05 manual (@wip TFK-07) |
| `Given the environment variable "ANTHROPIC_API_KEY" is not set` | LLM-06 (@wip TFK-07) |

**Ratatosk scout blackboard keys:** `evidence_plan`, `tool_calls`, `model_summary_chars`, `sources`, `scout_plan`.

**Config merge (CLI → env → repo `ratatosk.yaml` → `~/.ratatosk/config.yaml`):** see `ratatosk-config.feature`.

### Bootstrap MVP-W1 scenario IDs

```
CLI-01, CLI-04, CLI-06, CLI-07, CLI-08, CLI-09
DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, DISC-06, DISC-07, DISC-11, DISC-13, DISC-15, DISC-16, DISC-17, DISC-18, DISC-21
LLM-01, LLM-02, LLM-03, LLM-04  (@ollama @wip)
LLM-05, LLM-06  (@anthropic @wip)
CFG-02, CFG-06, CFG-07, CFG-08, CFG-09, CFG-10, CFG-11, CFG-12, CFG-13
```

Tag **`@ollama`** on LLM scenarios for optional CI. Default AT uses ScriptedDiscoveryLLM until BPE implements OllamaClient.

Feature files: `act-1-ratatosk/ratatosk-bootstrap.feature`, `ratatosk-discovery.feature`, `ratatosk-config.feature`, `ratatosk-model-summary.feature`, `ratatosk-scout.feature`, `act-6-cicd/ratatosk-update.feature`.

---

## Known Gaps → TFK-07

Gaps discovered during ESM-05 spec authoring. Implement via TFK-07 in BPE-04.

| # | Gap | ESM-05 workaround | TFK-07 deliverable |
|---|-----|-------------------|-------------------|
| 1 | `form_steps` adds `-input` suffix, but mockup login uses `login-email` (not `login-email-input`) | Specs use `the element "{test_id}" should be visible` for raw testid checks | Align `form_steps` to accept exact testids; or rename mockup inputs to follow `{field}-input` convention |
| 2 | No "screen ID assertion" step — can only check visible text | `Then the user should see "AUTH-LOGIN-1"` works if Screen ID is in HTML comment | Add step `Then the page shows screen "{screen_id}"` that checks `<!-- Screen: {id} -->` |
| 3 | MCP tool call steps do not exist | Narrative steps with tool name + JSON params table | New domain file `mcp_steps.py` with `When I call MCP tool "{tool}" with ...` |
| 4 | CLI subprocess steps do not exist | Narrative steps with exact command strings | Integration subprocess steps or `cli_steps.py` |
| 5 | E2E auth (`the user is logged in as "{role}"`) is not implemented | Not blocking for ESM-05 specs (AT auth works) | Implement once AUTH-LOGIN-1 ships in BPE |
| 6 | Delete modal confirm uses `confirm-delete-btn` not `dialog-confirm-btn` | Use `the element "confirm-delete-btn" should be visible` | Standardise delete modal testids or extend dialog steps with fallback (already partially done) |
