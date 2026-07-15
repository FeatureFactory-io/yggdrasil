# Yggdrasil: System Architecture Overview

**Version**: 0.1.0-inception
**Phase**: Inception — DTA complete, pending Gate B approval
**Date**: 2026-07-15
**Authors**: Dr. Dobbs v2 (DTA-01 → DTA-18)

---

## Executive Summary

Yggdrasil is an AI-augmented architecture knowledge-graph platform that keeps a living, queryable model of a software system synchronized with its codebase via CI/CD. The system is queried through a web GUI, a REST API, and an MCP interface usable from any AI client (Cursor, Claude Desktop, custom scripts).

**Key architectural decisions:**

- Modular Django monolith with strict bounded-context boundaries, deployed on AWS Elastic Beanstalk (blue/green)
- Two AI agents: Ratatosk (NER field agent, small/fast LLM) and Munin (ontology planner, larger LLM) — both behind a `LLMClient` protocol abstraction enabling swap to OpenAI, Ollama, or any provider
- Three distributable artifacts per release: backend container (ECR → EB), MCP facade container (GHCR, public), Ratatosk CLI (PyPI)
- Full offline/desktop mode: `docker-compose` + Ollama, zero cloud credentials required
- Aurora PostgreSQL with JSONB for flexible element properties; Redis for Celery async task queue and Django cache
- All writes (human, Ratatosk, MCP) go through the Munin / ChangeSet pipeline — graph integrity and audit trail are never bypassed

---

## 1. Application Blocks

**Pattern:** Modular monolith — single Django project, each bounded context is a Django app with strict import rules.

**Bounded contexts (Django apps):**

| App | Responsibility |
|---|---|
| `auth` | Session auth, personal access tokens (hashed), RBAC roles |
| `graph` | Element, Relationship, Stereotype, Package, Diagram — the core knowledge graph |
| `changeset` | ChangeSet, ChangeSetItem, LEARNED (MuninRule) — all write operations go through here |
| `munin` | Agentic planner: reads ChangeSet candidates, produces graph operations, maintains blackboard |
| `ratatosk` | RataskRun model, CLI integration models, run history |
| `mcp` | FastMCP server, `tools_handler.py` exposing the full service layer as MCP tools |
| `api` | DRF routers and serializers — REST interface consumed by GUI, Ratatosk CLI, and MCP facade |
| `llm` | `LLMClient` protocol + `AnthropicClient`, `OpenAIClient`, `OllamaClient` adapters |
| `web` | Django views, HTMX partials, templates, Cytoscape.js graph rendering |

**Dependency rules** (no circular imports allowed):

```
munin      → graph, changeset, llm
ratatosk   → graph, munin, llm
mcp        → graph, changeset, munin (via api service layer)
api        → graph, changeset, munin, ratatosk, auth
web        → api (via service layer), graph, changeset
auth       → standalone (no domain dependency)
llm        → standalone (no Django dependency in core protocol)
```

**UI architecture:**

- **Rendering:** server-rendered Django templates + HTMX partial updates. No SPA. Cytoscape.js used only for graph visualisation (client-rendered, data from REST).
- **Layout:** multi-panel (nav + content + detail drawer + collapsible Munin chat panel)
- **Component interaction:** HTMX `hx-swap` for list/filter updates; full page navigation for entity detail views

**Three distributable units:**

| Unit | Dockerfile | Registry | Consumers |
|---|---|---|---|
| Backend (web + Celery) | `Dockerfile` | ECR (private) → EB | Deployed by CI |
| MCP facade | `Dockerfile.mcp` | GHCR (public) | End users: `docker run` |
| Ratatosk CLI | `ratatosk/pyproject.toml` | PyPI + GitHub Release | End users: `pip install ratatosk` |

The MCP facade (`Dockerfile.mcp`) is intentionally minimal: FastMCP + httpx only, no Django, no ORM. It calls the Yggdrasil REST API over HTTP using a token.

---

## 2. Integration & API Design

**API style:** Hybrid

| Interface | Protocol | Consumers |
|---|---|---|
| `/api/v1/` | DRF REST, JSON | Web GUI, Ratatosk CLI, MCP facade |
| `/mcp` | FastMCP over HTTP (SSE) | AI clients connecting directly to cloud |
| Internal (service layer) | Python function calls | All apps share `*_service.py` via `tools_handler.py` |

**Versioning:** URL path — `/api/v1/`. No versioning on `/mcp` in MVP.

**Contract:** Code-first. `drf-spectacular` generates OpenAPI 3.0 from DRF serializers and views. Swagger UI served at `/api/docs/` in non-production environments only.

**LLM abstraction:**

```python
class LLMClient(Protocol):
    def complete(self, messages: list[Message], *, model: str, max_tokens: int) -> str: ...
    def stream(self, messages: list[Message], *, model: str) -> Iterator[str]: ...
```

Concrete implementations: `AnthropicClient` (default), `OpenAIClient`, `OllamaClient`. Selected via `LLM_PROVIDER` env var. Ratatosk and Munin each specify their preferred model tier via config; the abstraction routes the call.

**External integrations:** none in MVP. Ratatosk calls Yggdrasil REST API to fetch current model state before running analysis.

---

## 3. Code Organization

**Repository:** monorepo — single Git repository containing the Django project, Ratatosk CLI package, and CDK infra.

**Top-level layout:**

```
yggdrasil/
├── auth/                    # Django app: session auth, tokens, RBAC
├── graph/                   # Django app: core graph entities
├── changeset/               # Django app: ChangeSet pipeline, LEARNED rules
├── munin/                   # Django app: agentic planner, blackboard
├── ratatosk/                # Django app: run history + standalone CLI package
│   ├── pyproject.toml       # ratatosk PyPI package definition
│   ├── cli/                 # Click CLI entry points (bootstrap, update)
│   └── agent/               # NER + reconciliation logic
├── mcp/                     # Django app: FastMCP server
├── api/                     # Django app: DRF routers, serializers
├── llm/                     # LLMClient protocol + provider adapters
├── web/                     # Django app: views, HTMX partials, templates
├── infra/                   # CDK stacks (Python)
│   ├── app.py
│   ├── stacks/
│   │   ├── network_stack.py
│   │   ├── data_stack.py    # Aurora + ElastiCache Redis
│   │   ├── app_stack.py     # EB blue/green + ECR + CloudWatch log groups
│   │   └── cdn_stack.py     # CloudFront + ACM + Route53
│   └── requirements.txt
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── acceptance/          # behave-django AT; Step Library
│   ├── e2e/                 # behave + Playwright
│   ├── infra/               # CDK assertion tests
│   └── fixtures/
│       ├── seed.json        # session-level base data
│       ├── presets/         # suite-level presets
│       └── factories/       # FactoryBoy
├── scripts/                 # deploy-staging.sh, promote-prod.sh
├── docs/
│   └── architecture/
│       ├── SAO.md           # this file
│       └── decisions/       # ADR-NNN-title.md
├── logs/                    # app.log (gitignored)
├── Dockerfile               # backend (web + Celery worker)
├── Dockerfile.mcp           # MCP facade (FastMCP + httpx only)
├── docker-compose.yml       # local dev: Django + Celery + Redis + PostgreSQL + Ollama
├── docker-compose.prod.yml  # production template (ECR image)
├── pyproject.toml           # ruff, mypy, pytest, commitizen config
└── Makefile
```

**Naming conventions:**

| Kind | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `changeset_service.py` |
| Classes | `PascalCase` | `ChangeSetItem` |
| Functions/methods | `snake_case` | `apply_changeset` |
| Templates | `kebab-case.html` | `element-detail.html` |
| `data-testid` | `feature-area--role` | `changeset-review--accept-button` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_LLM_RETRIES` |

**Layer separation:** Views → Service layer (`*_service.py`) → Models. Views never access models directly. Service layer is also consumed by `tools_handler.py` so MCP and REST share identical business logic.

**Method size constraint:** public methods ≤ 30 lines; helpers extracted to private methods (`_` prefix). Enforced in code review.

---

## 4. Data Architecture

**Engine:** Aurora PostgreSQL (production, `db.t3.medium` serverless v2); PostgreSQL 16 via Docker for local dev and CI.

**ORM:** Django ORM. JSONB columns used for:

| Column | Model | Purpose |
|---|---|---|
| `properties` | `Element`, `Relationship` | Stereotype-driven flexible attributes |
| `property_schema` | `Stereotype` | JSON Schema definition for property validation |
| `allowed_edge_rules` | `Stereotype` | Which edge stereotypes are valid from this node |
| `detail` | `ChangeSetOperation` | Operation-specific payload (add/update/delete) |
| `blackboard` | `RataskRun` | Munin's intent task-list, written before acting, survives crashes |
| `rule_text` | `MuninRule` | Append-only LEARNED rules prepended to Munin's BASE prompt |

**Bitemporal history:** ChangeSet is the event log. Point-in-time queries (`?as_of=`) reconstruct graph state by replaying applied ChangeSets up to the target date. No separate temporal table — history is derived from the ChangeSet audit trail.

**Migrations:** Django migrations. Expand-contract pattern for breaking schema changes (add new column → backfill → remove old column across separate migrations).

**Test data:**

- Unit/integration: `factory_boy` factories, transaction rollback isolation per test
- E2E: `tests/fixtures/e2e_seed.json` loaded once before the suite; no ORM calls during E2E test execution; `make seed-e2e` target

**Connection pooling:** Django's default persistent connections (`CONN_MAX_AGE`). PgBouncer deferred to Phase II.

---

## 5. Test Strategy

**Model: Test Trophy** (TFK workflow — not the traditional Pyramid)

Integration tests are the main bet: they test the real thing without the GUI overhead. Unit tests are deliberately thin. Acceptance tests (AT) and E2E share the same tech stack — they differ in scope and intent, not in tooling.

```
E2E                            ← proves a user can complete a goal across multiple screens
Acceptance / AT                ← proves a single screen/feature works as expected
Integration (pytest)           ← all CRUD + ChangeSet paths; every PR; no mocks
Unit (pytest)                  ← pure logic, custom querysets, LLM adapters; every PR
CDK assertions                 ← infra stacks; every infra/** PR
```

**Why Trophy over Pyramid:**

- Unit tests prove isolation, not behaviour — `model.save()` returning OK tells nothing about persistence
- Integration tests hit the sweet spot: real DB + services, no browser, fast enough for CI
- AT and E2E tests are executable requirements via Gherkin — the `.feature` file IS the specification
- E2E is selective and slow; reserve for full multi-page user journeys on staging

**The shared test stack for AT and E2E:**

```
behave          — BDD framework: maps Gherkin scenarios to Python step definitions
behave-django   — runs the Django test server as part of the behave test suite
Playwright      — browser automation engine called inside E2E step definitions (not used in AT)
```

AT and E2E use the same `behave` + `behave-django` infrastructure. The distinction is **scope and intent**, not tooling:

| | Acceptance Test (AT) | E2E Test |
|---|---|---|
| **Goal** | Prove one screen / feature works correctly | Prove a user can complete a goal travelling through a sequence of screens |
| **Scope** | Single `.feature`, focused scenario | Multi-phase `.feature`, sequential across multiple pages |
| **Browser** | No — Django test client in step defs | Yes — Playwright in step defs |
| **Speed** | Fast | Slow (real browser, screenshots) |
| **When** | Every CI run (every PR) | Staging only, before `make swap` |
| **Models** | User operates one page | User completes a journey |

E2E tests explicitly model user behavior: each scenario represents a goal a real user (Priya, Marcus, Elena) wants to achieve — e.g. "Priya bootstraps a repo, reviews the ChangeSet, and confirms the model reflects her codebase." The test passes only when the user's goal is demonstrably achieved, not just when individual pages render.

**Runner summary:**

| Layer | Runner | Notes |
|---|---|---|
| Unit | pytest + pytest-django | Thin — no testing framework behaviour, no auto-generated view tests |
| Integration | pytest + Django test client | Real PostgreSQL, real services; **no mocks** |
| AT | behave + behave-django | Step Library; Django test client in steps; no browser |
| E2E | behave + behave-django + Playwright | Playwright in steps; screenshot after every step; `--base-url` parameterised (local / staging / prod) |
| CDK infra | `aws_cdk.assertions` | Synthesise in-memory; no AWS credentials |

**Test directory structure:**

```
tests/
├── unit/
├── integration/
├── acceptance/                  # behave-django AT
│   ├── features/
│   │   └── steps/               # TAF Step Library
│   │       ├── navigation_steps.py
│   │       ├── form_steps.py
│   │       ├── table_steps.py
│   │       ├── auth_steps.py
│   │       ├── assertion_steps.py
│   │       └── dialog_steps.py
│   └── environment.py
├── e2e/                         # behave + Playwright
│   ├── features/
│   │   └── steps/
│   └── environment.py           # Playwright browser setup, screenshot on every step
├── fixtures/
│   ├── seed.json                # Session-level base data (loaded once in before_all)
│   ├── presets/                 # Suite-level presets (team_preset.json, empty_preset.json)
│   └── factories/               # FactoryBoy — test-level dynamic data
│       ├── user_factory.py
│       └── model_factories.py
├── infra/                       # CDK assertion tests
└── conftest.py
```

**Fixture scopes:**

| Scope | Mechanism | When |
|---|---|---|
| Session | `seed.json` via `loaddata` in `before_all` | Loaded once; reference / base data |
| Suite | `presets/*.json` | Loaded for a related group of tests |
| Test | FactoryBoy factories, transaction rollback | Per test; unique data, no collisions |

**Key rules:**

- No mocks in integration or AT tests (`do-not-mock-in-integration-tests.mdc`)
- All pytest runs write to `tests.log` (`do-continuous-testing.mdc`)
- `data-testid` on every interactive control, hierarchical naming (`do-semantic-versioning-on-ui-elements.mdc`)
- BDD `.feature` file in `docs/features/act-X/` must exist before implementation begins (`do-write-scenarios.mdc`)
- Coverage quality over quantity — 90% coverage with useless tests is worse than 60% with real integration tests

**Coverage targets:** thin unit coverage on pure logic only; 100% of CRUD + ChangeSet paths covered by integration tests; all `.feature` scenarios passing AT; 5 E2E journeys on staging before release.

**CI gates:**

| Stage | When | Gate |
|---|---|---|
| Unit + Integration + AT | Every PR | All must pass before container build |
| E2E | After `deploy-idle` on staging | Must pass before `make swap` is available |
| CDK assertions | Every `infra/**` PR | Must pass before `cdk deploy` |

---

## 6. Performance & Scalability

**Load profile:** Low concurrency at launch (enterprise internal tool, tens of simultaneous users). Munin agentic loops and Ratatosk NER passes are the dominant workload — potentially 30–120s LLM call sequences.

**Async processing:**

- Celery with Redis broker (same Redis instance as Django cache)
- Munin agentic loops and Ratatosk runs execute as Celery tasks — HTTP requests return a `run_id` immediately; client polls `get_ratatosk_run` or monitors the GUI
- `docker-compose` includes a Celery worker service; production EB runs Celery worker as a second process in the same container (single-instance MVP)

**Caching:** Django cache framework backed by Redis. Metamodel reads (stereotypes, packages) cached with short TTL (5 min). No HTTP-level caching (HTMX partial responses must be fresh).

**Local / desktop mode:** `docker-compose up` starts Django, Celery worker, Redis, PostgreSQL, and Ollama. `LLM_PROVIDER=ollama` routes all LLM calls to the local Ollama container. Zero cloud credentials required.

**Scaling path (Phase II):** EB auto-scaling group (≥ 2 instances), dedicated Celery worker EB environment, Aurora read replica, ElastiCache replica, separated Celery worker from web process.

---

## 7. Error Handling & Resilience

**Error taxonomy:**

| Category | HTTP Status | Log Level | User-facing |
|---|---|---|---|
| Domain (business rule violation) | 422 | WARNING | Yes, with explanation |
| Validation (input invalid) | 400 | INFO | Yes, field-level detail |
| Not Found | 404 | INFO | Yes |
| Auth/Authz | 401/403 | WARNING | Generic message only |
| LLM provider error | — (async) | ERROR | Surfaced in run status |
| Infrastructure | 500 | ERROR | Generic; details in logs only |

**Standard error envelope (REST API):**

```json
{
  "error": {
    "code": "ELEMENT_NOT_FOUND",
    "message": "Element with id 'abc-123' does not exist in model 'Yggdrasil'",
    "details": {},
    "request_id": "req-7f3a9b2c"
  }
}
```

**LLM retry policy:** exponential backoff with jitter, max 3 attempts, 1s/2s/4s base delays. Circuit breaker opens after 5 consecutive provider errors within 60s; half-open probe every 30s.

**Munin crash recovery:** blackboard (`RataskRun.blackboard`) is a JSON task list written before each step and updated as steps complete. On restart, Munin reads the blackboard and resumes from the last incomplete step. Blackboard is visible in the run history GUI for transparency.

**ChangeSet atomicity:** all operations in a ChangeSet apply inside a single DB transaction. Failure rolls back the entire apply; the ChangeSet status is set to `failed` with the error detail.

**Idempotency:** ChangeSet operations are idempotent — re-applying an already-applied ChangeSet is a no-op (detected by checking operation status).

---

## 8. Infrastructure

**Cloud provider:** AWS (us-east-1 default).

**CDK stacks (Python):**

```
NetworkStack  → VPC, public/private subnets, security groups (EB-SG, RDS-SG, Redis-SG)
DataStack     → Aurora PostgreSQL (serverless v2, private subnet) + ElastiCache Redis (private subnet)
AppStack      → ECR repo, EB application + blue/green environments, IAM roles, CloudWatch log groups + alarms
CdnStack      → ACM certificate, CloudFront distribution, Route53 CNAME (Lambda custom resource)
```

**Elastic Beanstalk blue/green:**

- Two environments: `yggdrasil-blue`, `yggdrasil-green`
- One environment always holds the `yggdrasil-prod.{region}.elasticbeanstalk.com` CNAME prefix (the live environment)
- `make swap` calls `aws elasticbeanstalk swap-environment-cnames` — reassigns the `yggdrasil-prod` CNAME prefix to the other environment. CloudFront origin and Route53 record are never modified during a release.
- Platform: Amazon Linux 2023 / Docker; `t3.small` single-instance for MVP
- Log streaming: `aws:elasticbeanstalk:cloudwatch:logs StreamLogs=true`, 30-day retention

**DNS / TLS:**

```
yggdrasil.featurefactory.io  (Route53 CNAME → CloudFront, set once)
         ↓
CloudFront distribution  (ACM wildcard cert, HSTS, caching disabled, all HTTP methods)
         ↓
yggdrasil-prod.{region}.elasticbeanstalk.com  (static origin, never changes)
         ↓
[yggdrasil-blue  OR  yggdrasil-green]  ← swap moves "prod" prefix between these
```

**Local dev:** `docker-compose.yml` with services: `web` (Django), `worker` (Celery), `redis`, `db` (PostgreSQL 16), `ollama`. No AWS dependency for local development.

**Makefile targets:**

| Target | Action |
|---|---|
| `make provision` | Install all local deps (uv sync + docker pull) |
| `make run` | `docker-compose up` (full local stack) |
| `make test` | pytest unit + integration → `tests.log` |
| `make test-unit` | pytest unit only |
| `make test-integration` | pytest integration only |
| `make test-at` | behave-django acceptance tests |
| `make test-e2e` | behave + Playwright E2E (requires `BASE_URL=`) |
| `make lint` | ruff check |
| `make format` | ruff format |
| `make seed` | Load `tests/fixtures/seed.json` (session base data) |
| `make infra-diff` | `cdk diff` (no AWS changes) |
| `make infra-deploy` | `cdk deploy --all` |
| `make staging` | Deploy current HEAD to inactive EB env + smoke test |
| `make swap` | Promote inactive EB env to production (CNAME swap + smoke) |
| `make export-data` | JSON dump of full graph |

---

## 9. CI/CD Pipeline

**Platform:** GitHub Actions

**Three parallel release tracks** (all triggered by a published GitHub Release tag `x.y.z`):

```
Tag published
    ├── Track 1: Backend
    │       lint → test-unit + test-integration + test-at (all must pass)
    │       → build Dockerfile → push ECR
    │       → deploy-idle EB env → E2E on staging (behave + Playwright)
    │       → (manual gate) → make swap → prod smoke
    │
    ├── Track 2: MCP Facade
    │       build Dockerfile.mcp → push GHCR (ghcr.io/yggdrasil/yggdrasil-mcp:latest + :x.y.z)
    │
    └── Track 3: Ratatosk CLI
            build ratatosk/ wheel + sdist → publish PyPI → attach to GitHub Release assets
```

**PR / push to main:** `lint → test-unit + test-integration + test-at` (all three must pass); build only — no publish, no EB deploy.

**CDK infra pipeline:** separate workflow on `infra/**` changes — CDK assertion tests → `cdk diff` (informational) → manual `cdk deploy` gate.

**Artifact registries:**

| Artifact | Registry | Visibility |
|---|---|---|
| Backend container | ECR (`yggdrasil`) | Private |
| MCP facade container | GHCR (`ghcr.io/yggdrasil/yggdrasil-mcp`) | Public |
| Ratatosk CLI wheel | PyPI (`ratatosk`) + GitHub Release assets | Public |

**CI glue philosophy:** GitHub Actions YAML is thin — each job calls a `make` target or `scripts/` shell script. Logic lives in the repo, not in CI YAML.

**Security scanning:** `pip-audit` runs on every PR as part of the lint stage.

---

## 10. Release & Rollback

**Deployment strategy:** Blue-green CNAME swap at the EB environment level.

**Release procedure:**

```
git tag x.y.z && git push origin x.y.z
  → GitHub Release published
  → CI: test → build all three artifacts → deploy to idle EB env → staging smoke
  → Human reviews staging URL
  → make swap  (or trigger promote.yml workflow_dispatch)
  → SHA guard checks staging VersionLabel matches expected SHA
  → aws elasticbeanstalk swap-environment-cnames
  → prod smoke: GET /health/ compares revision to staging revision
```

**Rollback:** `make swap` again — re-swaps CNAME back to previous EB environment. Traffic switch completes in < 60s. Previous environment remains running until the next deploy cycle.

**Versioning:** Semantic versioning (MAJOR.MINOR.PATCH). Git tags drive all three release tracks. GitHub Release notes auto-generated from Angular conventional commits (enforced via `commitizen` pre-commit hook).

**Hotfix:** push fix to main → `make staging` (deploys HEAD to idle env) → smoke → `make swap`.

**DB migrations:** applied as a `post-deploy` hook in the EB platform config before the new application version starts serving traffic. Expand-contract pattern ensures migrations are safe to run against the old code version.

---

## 11. Observability

**Logging — two sinks (both always active):**

| Sink | Format | Scope |
|---|---|---|
| `logs/app.log` (rotating) | structlog text | All environments; cleared on restart for clean local diagnosis |
| CloudWatch Log Groups | structlog JSON | Production; EB streams automatically to `/aws/elasticbeanstalk/{env}/...` |

**Log level policy:** INFO at every service method entry/exit and decision point. DEBUG for LLM prompt/response detail (disabled in production). ERROR for unexpected exceptions with full traceback.

**Key structured log events:**

| Event | Fields |
|---|---|
| ChangeSet applied | `changeset_id`, `model_id`, `ops_count`, `source`, `duration_ms` |
| Munin blackboard step | `run_id`, `step`, `status`, `tokens_used` |
| Ratatosk run start/end | `run_id`, `model`, `trigger`, `delta_buckets` |
| LLM call | `provider`, `model`, `prompt_tokens`, `completion_tokens`, `latency_ms` |
| HTTP request | `request_id`, `method`, `path`, `status_code`, `duration_ms`, `user_id` |

**Correlation:** `request_id` generated in Django middleware and threaded through all log lines within a request context. Celery tasks carry `task_id` as correlation.

**CloudWatch alarms:**

| Alarm | Threshold | Action |
|---|---|---|
| `yggdrasil-app-error-rate` | > 2 ERROR log entries / hour | SNS → email (P1) |
| EB environment health | Degraded / Severe | SNS → email (P1) |

**Dashboards:** CloudWatch Dashboards for EB metrics (request count, 5xx rate, CPU). No external tool in MVP.

---

## 12. Config & Secrets

**Local development:**

```bash
# .env (gitignored)
DEBUG=True
DATABASE_URL=postgresql://yggdrasil:yggdrasil@localhost:5432/yggdrasil
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-only-insecure-key
LLM_PROVIDER=ollama          # or anthropic, openai
ANTHROPIC_API_KEY=           # optional for local
OLLAMA_BASE_URL=http://ollama:11434
```

**Production:** AWS Secrets Manager secrets injected as EB environment properties at deploy time (same pattern as Huginn's `scripts/deploy-staging.sh` SSM fetch).

**Validated at startup:** `django-environ` raises `ImproperlyConfigured` for any missing required variable. The startup sequence fails fast before accepting traffic.

**Secrets inventory:**

| Secret | Manager path | Required |
|---|---|---|
| `SECRET_KEY` | `/yggdrasil/SECRET_KEY` | Always |
| `DATABASE_URL` | `/yggdrasil/DATABASE_URL` | Always |
| `REDIS_URL` | `/yggdrasil/REDIS_URL` | Always |
| `ANTHROPIC_API_KEY` | `/yggdrasil/ANTHROPIC_API_KEY` | If `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | `/yggdrasil/OPENAI_API_KEY` | If `LLM_PROVIDER=openai` |

**Feature flags:** config-based (env var boolean) in MVP. No external flag service.

---

## 13. Security

**Authentication:**

| Client | Mechanism |
|---|---|
| Web browser | Django session (cookie-based) |
| Ratatosk CLI | Personal access token (`Authorization: Bearer <token>`) |
| MCP facade | Personal access token (passed as env var to container) |
| MCP direct | Personal access token (`Authorization: Bearer <token>`) |
| CI agents | Personal access token (stored as GitHub Actions secret) |

Token storage: SHA-256 hash stored in DB. Raw token shown once on creation, never retrievable. Scope: `read_only` or `read_write`.

**Authorization (RBAC):**

| Role | Permissions |
|---|---|
| `admin` | Manage users, groups, tokens; all write operations |
| `architect` | Full read + write on Models, Elements, Relationships, ChangeSets |
| `viewer` | Read-only across all resources |

Object-level: each Model has an owner group; non-admin users can only write to Models their group owns.

**API security:**

- Rate limiting per token: `django-ratelimit`, 100 req/min write, 500 req/min read
- CSRF: Django's built-in CSRF middleware for session-authenticated routes; exempt for token-authenticated API routes
- CORS: locked to known origins (`yggdrasil.featurefactory.io`) in production
- Content Security Policy: strict CSP headers via Django middleware
- HTTPS enforced: CloudFront redirects HTTP → HTTPS; HSTS 1-hour (starter, escalate post-launch)

**Dependency scanning:** `pip-audit` runs on every PR in the lint stage. Fail on any known high/critical CVE.

---

## 14. Backup & Recovery

**Aurora automated backups:**

- Continuous backup (WAL archiving) — Aurora default
- Daily snapshots, 7-day retention (AWS managed)
- Point-in-time recovery (PITR) enabled — **RPO: 5 minutes**

**Recovery targets:**

| Metric | Target | Mechanism |
|---|---|---|
| RPO | 5 minutes | Aurora PITR |
| RTO | 1 hour | Restore Aurora snapshot + redeploy EB env |

**Multi-AZ:** deferred to Phase II. MVP runs single-AZ with PITR as the primary safety net.

**Data export:** `make export-data` produces a JSON dump of the full graph (all Elements, Relationships, ChangeSets, LEARNED rules for all Models). Serves as a portable backup independent of Aurora.

**DR procedure (documented in `docs/architecture/decisions/` runbook):**

1. Restore Aurora cluster from PITR or snapshot
2. Update `DATABASE_URL` secret in Secrets Manager
3. `make staging` (deploys current HEAD to idle EB env with new DB URL)
4. Smoke test data integrity
5. `make swap`

---

## 15. Developer Experience

**Recommended IDE:** Cursor (`.cursor/` config present in repo).

**Toolchain:**

| Tool | Purpose | Config |
|---|---|---|
| `ruff` | Lint + format | `pyproject.toml` |
| `mypy` | Type checking | `pyproject.toml` |
| `commitizen` | Enforce Angular commits | `pyproject.toml` |
| `pre-commit` | Run ruff, mypy, commitizen on commit | `.pre-commit-config.yaml` |
| `pytest` | All test layers | `pyproject.toml` / `pytest.ini` |
| `uv` | Fast dependency management | `uv.lock` |

**Inner loop:**

1. `git clone && make provision` — install all deps, pull Docker images (target: < 5 min)
2. `make run` — `docker-compose up` starts full local stack including Ollama
3. `make test` — pytest, output to `tests.log`
4. Django runserver auto-reloads on file changes; HTMX partials testable with Django test client (no browser)

**Time-to-first-feature target:** < 2 hours from `git clone`.

**Template checklist (enforced in PR review):**

- Every interactive control has `data-testid` (format: `feature-area--role`, e.g. `changeset-review--accept-button`)
- Every button has `aria-label`; disabled buttons have a Bootstrap tooltip explaining why and how to enable
- No CSS/XPath selectors in E2E tests — `get_by_test_id` first

**Skeleton-first development (`do-skeletons-first.mdc`):** new classes/methods ship as documented stubs (`raise NotImplementedError()`) with full Sphinx docstrings, type hints, and inline logic comments before implementation begins.

---

## 16. Documentation Strategy

**Architecture Decision Records (ADRs):**

- Location: `docs/architecture/decisions/ADR-NNN-title.md`
- Template: Title / Status / Context / Decision / Consequences
- Trigger: any significant technology or architecture choice
- Review: PR-based, no separate meeting required

**API documentation:**

- `drf-spectacular` generates OpenAPI 3.0 from DRF code
- Swagger UI at `/api/docs/` (non-production only)
- MCP tools documented inline in `mcp/tools_handler.py` docstrings; auto-surfaced via FastMCP

**Code documentation standards (`do-docstring-format.mdc`, `keep-docstrings-consistent.mdc`):**

```python
def apply_changeset(changeset_id: str, *, applied_by: str) -> ChangeSet:
    """
    Apply all pending operations in a ChangeSet to the graph inside a transaction.

    :param changeset_id: UUID of the ChangeSet to apply. Example: "cs-7f3a9b2c"
    :param applied_by: Username or token name of the actor. Example: "priya@example.com"
    :return: Updated ChangeSet with status='applied'. Example: ChangeSet(id="cs-7f3a9b2c", status="applied")
    :raises ChangeSetNotFound: if changeset_id does not exist
    :raises ChangeSetAlreadyApplied: if status is already 'applied'
    :raises IntegrityError: if any graph operation violates DB constraints (transaction rolled back)
    """
```

**README hierarchy:** root `README.md` (onboarding, `make provision` → `make run`) → per-app `README.md` → `docs/` (architecture, runbooks).

**Runbook location:** `docs/runbooks/` — format: Trigger / Impact / Steps / Verification. Updated after every incident.

---

## Technology Stack Table

> Machine-readable. Consumed by Bootstrap Project (BSP) for automated provisioning.

| Layer | Tool | Version | Install (macOS) | Install (Linux) | Verify |
|---|---|---|---|---|---|
| Language | Python | 3.12+ | `brew install python@3.12` | `apt install python3.12` | `python3 --version` |
| Web framework | Django | 5.1+ | `pip install django` | `pip install django` | `django-admin version` |
| REST API | djangorestframework | 3.15+ | `pip install djangorestframework` | `pip install djangorestframework` | `python -c "import rest_framework; print(rest_framework.VERSION)"` |
| OpenAPI | drf-spectacular | 0.27+ | `pip install drf-spectacular` | `pip install drf-spectacular` | `pip show drf-spectacular` |
| MCP server | fastmcp | 2.x | `pip install fastmcp` | `pip install fastmcp` | `python -c "import fastmcp"` |
| HTMX | htmx | 2.x | (CDN / static) | (CDN / static) | browser devtools |
| Graph viz | Cytoscape.js | 3.x | (CDN / static) | (CDN / static) | browser devtools |
| CSS | Bootstrap | 5.3+ | (CDN / static) | (CDN / static) | browser devtools |
| Async tasks | celery | 5.x | `pip install celery` | `pip install celery` | `celery --version` |
| Cache/broker | Redis | 7.x | `brew install redis` | `apt install redis-server` | `redis-cli ping` |
| LLM (Anthropic) | anthropic | 0.30+ | `pip install anthropic` | `pip install anthropic` | `pip show anthropic` |
| LLM (OpenAI) | openai | 1.x | `pip install openai` | `pip install openai` | `pip show openai` |
| LLM (local) | Ollama | latest | `brew install ollama` | `curl -fsSL https://ollama.ai/install.sh \| sh` | `ollama --version` |
| HTTP client | httpx | 0.27+ | `pip install httpx` | `pip install httpx` | `pip show httpx` |
| Config | django-environ | 0.11+ | `pip install django-environ` | `pip install django-environ` | `pip show django-environ` |
| DB (prod) | Aurora PostgreSQL | 16 | (AWS managed) | (AWS managed) | `psql --version` |
| DB (local) | PostgreSQL | 16+ | `brew install postgresql@16` | `apt install postgresql` | `psql --version` |
| IaC | aws-cdk-lib | 2.x | `pip install aws-cdk-lib` | `pip install aws-cdk-lib` | `cdk --version` |
| IaC runtime | Node.js | 20 LTS | `brew install node@20` | `apt install nodejs` | `node --version` |
| CI/CD | GitHub Actions | — | (cloud) | (cloud) | — |
| Container runtime | Docker | 24+ | `brew install --cask docker` | `apt install docker.io` | `docker --version` |
| Test runner | pytest | 8+ | `pip install pytest` | `pip install pytest` | `pytest --version` |
| Test (Django) | pytest-django | 4.x | `pip install pytest-django` | `pip install pytest-django` | `pip show pytest-django` |
| Test (AT + E2E) | behave | 1.x | `pip install behave` | `pip install behave` | `behave --version` |
| Test (AT + E2E) | behave-django | 1.x | `pip install behave-django` | `pip install behave-django` | `pip show behave-django` |
| Test (E2E browser) | Playwright | 1.x | `pip install playwright && playwright install chromium` | same | `playwright --version` |
| Test data | factory-boy | 3.x | `pip install factory-boy` | `pip install factory-boy` | `pip show factory-boy` |
| Linter | ruff | 0.6+ | `pip install ruff` | `pip install ruff` | `ruff --version` |
| Type checker | mypy | 1.x | `pip install mypy` | `pip install mypy` | `mypy --version` |
| Dep manager | uv | 0.4+ | `brew install uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |
| Commit convention | commitizen | 3.x | `pip install commitizen` | `pip install commitizen` | `cz version` |
| Pre-commit | pre-commit | 3.x | `pip install pre-commit` | `pip install pre-commit` | `pre-commit --version` |
| Dep security | pip-audit | 2.x | `pip install pip-audit` | `pip install pip-audit` | `pip-audit --version` |
| VCS | git | 2.x | `brew install git` | `apt install git` | `git --version` |
| Build | make | 4+ | (bundled) | `apt install make` | `make --version` |

---

## Skill Coverage Report

| Domain | Covered by Huginn/Mimir patterns | Gaps |
|---|---|---|
| Application Blocks | Django modular monolith (Huginn) ✅ | LLM abstraction protocol — custom ❌ |
| Integration & API | DRF REST + FastMCP (Mimir) ✅ | drf-spectacular setup — custom ❌ |
| Code Organization | Huginn repo structure ✅ | ratatosk/ standalone package layout — custom ❌ |
| Data Architecture | Django ORM + PostgreSQL (Huginn) ✅ | JSONB property schema validation — custom ❌ |
| Test Strategy | pytest + behave-django + Playwright (TFK Trophy model) ✅ | CDK assertion tests — custom ❌ |
| Performance & Scalability | Celery + Redis (Mimir) ✅ | Ollama local mode integration — custom ❌ |
| Error Handling & Resilience | DRF error handling (Mimir) ✅ | LLM circuit breaker — custom ❌ |
| Infrastructure | Huginn CDK stacks ✅ | ElastiCache in DataStack — custom ❌ |
| CI/CD Pipeline | Mimir build-and-deploy.yml ✅ | Ratatosk PyPI publish track — custom ❌ |
| Release & Rollback | Huginn promote-prod.sh / make swap ✅ | None |
| Observability | Huginn CloudWatch log groups + alarms ✅ | structlog → app.log rotating handler — custom ❌ |
| Config & Secrets | Huginn SSM + django-environ ✅ | None |
| Security | Django auth + token pattern (Mimir) ✅ | RBAC permission matrix — custom ❌ |
| Backup & Recovery | Aurora PITR (AWS managed) ✅ | make export-data JSON dump — custom ❌ |
| Developer Experience | Huginn Makefile + Mimir pyproject.toml ✅ | data-testid template checklist — custom ❌ |
| Documentation Strategy | Mimir docstring pattern ✅ | ADR process — custom ❌ |

**Gap summary:** 10 custom patterns to establish. None are high-risk; all have clear prior art in Huginn/Mimir. Estimated additional effort: +2 iterations.

---

## Key Decisions with Rationale

| Decision | Choice | Rationale |
|---|---|---|
| Architectural pattern | Modular monolith | Team size and scope don't justify microservices; bounded contexts provide clear growth path |
| Web rendering | Server-rendered + HTMX | Testability (Django test client, no browser for most tests); avoids SPA complexity |
| Graph visualisation | Cytoscape.js (client-rendered) | Interactive graph exploration requires client-side rendering; server-generated SVG too static |
| LLM abstraction | `LLMClient` protocol | Enables local Ollama for dev/offline, swap to cheaper model for Ratatosk, upgrade Munin independently |
| Async broker | Redis (not SQS) | Dev/prod parity; local docker-compose works without AWS; Redis doubles as Django cache |
| Infrastructure | AWS EB + Aurora | Proven in Huginn/Mimir; blue/green swap at zero cost; Aurora PITR covers RPO |
| IaC | CDK (Python) | Consistent language with Django codebase; Huginn's CDK stacks are a direct reference implementation |
| CI/CD | GitHub Actions | Yggdrasil is a GitHub repo; mirrors Mimir's `build-and-deploy.yml` pattern |
| Release strategy | EB CNAME swap (`make swap`) | Zero-downtime; instant rollback by re-swapping; < 60s RTO |
| MCP distribution | `Dockerfile.mcp` → GHCR | Users run locally without exposing cloud credentials to their MCP client |
| Ratatosk distribution | PyPI + GitHub Release | `pip install ratatosk` is the natural CI pipeline install pattern |
| Token storage | SHA-256 hash, shown once | Industry standard; no plaintext storage; revocation without key rotation |
| Bitemporal history | ChangeSet event log | Avoids separate temporal tables; `?as_of=` queries reconstruct state by replay |
| Test model | Test Trophy (integration-heavy) | Integration tests prove behaviour with real DB/services; unit tests are thin; AT makes `.feature` files executable requirements |
| Test isolation | Transaction rollback (unit/integration/AT), `seed.json` + presets (E2E) | Fast, deterministic, no mock leakage |

---

## Discovered Patterns & Lessons Learned

*Reserved — populated during and after implementation.*

### Critical Discoveries

*(None yet — implementation has not begun.)*

### Retrospective Updates

*(None yet — DTA decisions are pre-implementation.)*

---

*Gate B: this document requires explicit user approval before DSP (Define Software Process) begins.*
