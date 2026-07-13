# Yggdrasil: System Architecture Overview

**Version:** 0.1.0 (Inception)  
**Status:** Approved for Elaboration  
**Produced by:** DTA-18

## Executive Summary

Yggdrasil is an AI-maintained organizational knowledge repository — a living graph of elements and relationships bootstrapped by Ratatosk and queryable via REST, MCP, and a Django HTMX GUI. Architecture: **modular monolith** with DRF as the engine, graph-over-Postgres (bitemporal), deployed on **Elastic Beanstalk + RDS**.

**Key decisions:**
- DRF REST is the single source of behavior; FastMCP and Ratatosk are HTTP clients
- Graph stored as Element/Relationship ORM models with JSONB + recursive CTE traversal
- Bitemporal append-only versioning on all graph facts
- ChangeSet queue for Ratatosk writes with confidence-based auto-apply
- EB blue/green via CNAME swap; release-gated CI/CD

---

## 1. Application Blocks

**Pattern:** Modular monolith (Django)

| App | Responsibility |
|-----|----------------|
| `graph` | Core models: Element, Relationship, Stereotype, Package, Diagram, ChangeSet |
| `api` | DRF viewsets, traversal service, permissions |
| `web` | HTMX views, Cytoscape, AI chat UI |
| `core` | Shared utilities, `llm/` provider abstraction |
| `mcp` | FastMCP server entrypoint (calls api via HTTP) |
| `ratatosk` | Separate pip package; CLI connectors (HTTP only) |

**Dependency rules:** `api`, `web`, `mcp` → `graph`; `ratatosk` → external HTTP only.

**UI:** Server-rendered HTMX + Bootstrap 5 + Cytoscape.js; partial updates for CRUDLF.

---

## 2. Integration & API Design

**API style:** REST (DRF) with OpenAPI via drf-spectacular.

**Core endpoints:**
- `/api/v1/elements/`, `/api/v1/relationships/`
- `/api/v1/stereotypes/`, `/api/v1/packages/`, `/api/v1/diagrams/`
- `/api/v1/changesets/` (review queue)
- `/api/v1/traverse/` (from, depth, as_of)
- `/api/v1/views/{package}/` (filtered browse)

**MCP:** FastMCP tools wrap REST (`get_element`, `traverse`, `search`).

**Ratatosk:** CLI `ratatosk scan gitlab --project X` → POST ChangeSet.

**Versioning:** URL prefix `/api/v1/`; breaking changes → v2.

---

## 3. Code Organization

```
yggdrasil/                 # repo root
├── manage.py
├── yggdrasil/             # Django project settings
├── graph/                 # domain models + services
├── api/                   # DRF
├── web/                   # HTMX templates/views
├── core/                  # llm, logging helpers
├── mcp_server/            # FastMCP entry
├── ratatosk/              # pip-installable CLI package
├── infra/                 # AWS CDK (Python)
├── tests/
├── docs/
├── templates/
└── static/
```

Layers: `models` → `services` → `serializers` / `views`.

---

## 4. Data Architecture

**Engine:** PostgreSQL 16+ on RDS.

**Models:**
- `Element` (Vertex): name, stereotype FK, package FK, properties JSONB, bitemporal fields, provenance
- `Relationship` (Edge): from_element, to_element, stereotype, properties JSONB, bitemporal, provenance
- `Stereotype`: name, property_schema JSONB, allowed_edges JSONB
- `Package`: name, parent FK (tree), slug
- `Diagram`: package FK, cytoscape_layout JSONB
- `ChangeSet`: status, source, items JSONB, confidence aggregate

**Bitemporal:** `valid_from`, `valid_to` (null = current), `recorded_at`.

**Traversal:** `graph.services.traversal` uses recursive CTEs.

**Indexes:** GIN on `properties`; btree on stereotype, package, valid_from/valid_to.

**Migrations:** Django migrations; seed stereotypes via data migration.

**Escape hatch:** Apache AGE extension if CTE performance insufficient.

---

## 5. Test Strategy

- **Unit:** pytest, graph services, LLM provider mocks
- **API:** DRF APIClient, permission matrix cases
- **E2E:** Playwright against HTMX pages (CRUDLF scenarios from ESM)
- **Coverage target:** 80% on `graph` and `api`

---

## 6. Performance & Scalability

- Pagination: 50 items default, max 200
- Traversal depth cap: 10 hops default
- JSONB GIN indexes for property filters
- Future: Redis cache for hot traverse queries

---

## 7. Error Handling & Resilience

- DRF exception handler → consistent JSON errors
- Stereotype schema validation on element write
- ChangeSet: transactional apply; rollback on partial failure
- Ratatosk: retry 3x with exponential backoff on API errors

---

## 8. Infrastructure

**Provider:** AWS  
**Region:** us-east-1  
**Compute:** Elastic Beanstalk (Docker platform)  
**Database:** RDS PostgreSQL 16  
**Registry:** ECR  
**DNS:** Route53  
**Style:** EB blue/green (see INFRA_REQUIREMENTS.md)

---

## 9. CI/CD Pipeline

**Trigger:** Release-gated (`gh release create vX.Y.Z`)  
**Stages:** test → build (ECR) → deploy-idle → smoke → manual promote → prod smoke  
See CICD_REQUIREMENTS.md.

---

## 10. Release & Rollback

EB `swap-environment-cnames` between prod and idle environments. Rollback = swap back + prior image tag redeploy.

---

## 11. Observability

Three-tier logging to CloudWatch:
1. **App:** structured JSON, request_id, user
2. **GUI:** HTMX interaction events (screen_id, action)
3. **Token:** LLM provider, model, tokens_in/out per chat/Ratatosk call

Health endpoint: `/health/` returns `{"status":"ok","revision":GIT_REVISION}`.

---

## 12. Config & Secrets

django-environ from `.env` / EB environment properties:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres connection |
| `DJANGO_SECRET_KEY` | Django secret |
| `LLM_PROVIDER` | `qwen` or `anthropic` |
| `LLM_BASE_URL` | Provider endpoint |
| `LLM_MODEL` | Model name |
| `LLM_API_KEY` | API key |

---

## 13. Security

- Django session auth (MVP); JWT later
- **Permission matrix:** Django Groups × Stereotype CRUDL via custom DRF permission class
- **PBAC:** Filter querysets where `properties__confidential=true` unless user in Executives group
- HTTPS via EB ALB + ACM
- CSRF on web forms; API token auth for Ratatosk/MCP

---

## 14. Backup & Recovery

- RDS automated backups, 7-day retention
- Pre-migrate SSM backup to S3 (CI/CD)
- Bitemporal graph enables as-of recovery queries

---

## 15. Developer Experience

- `make run`, `make test`, `make lint`, `make migrate`
- ruff format + lint; pre-commit hooks
- Local dev: SQLite optional, Postgres preferred via docker-compose
- Local LLM: Qwen via `LLM_BASE_URL=http://localhost:11434/v1`

---

## 16. Documentation Strategy

- `docs/` for UX and architecture (ESM/DTA artifacts)
- SAO.md living document with retrospective section
- OpenAPI at `/api/schema/` via drf-spectacular
- README quickstart for Ratatosk CLI

---

## Technology Stack Table

| Layer | Tool | Version | Install (macOS) | Verify |
|-------|------|---------|-----------------|--------|
| Language | Python | 3.12+ | `brew install python@3.12` | `python3 --version` |
| Framework | Django | 5.1+ | `pip install django` | `django-admin --version` |
| API | djangorestframework | 3.15+ | `pip install djangorestframework` | `pip show djangorestframework` |
| API docs | drf-spectacular | 0.27+ | `pip install drf-spectacular` | `pip show drf-spectacular` |
| DB driver | psycopg | 3.2+ | `pip install psycopg[binary]` | `pip show psycopg` |
| MCP | fastmcp | 2.0+ | `pip install fastmcp` | `pip show fastmcp` |
| HTTP | httpx | 0.27+ | `pip install httpx` | `pip show httpx` |
| DB | PostgreSQL | 16+ | `brew install postgresql@16` | `psql --version` |
| Test | pytest | 8+ | `pip install pytest pytest-django` | `pytest --version` |
| E2E | Playwright | 1.40+ | `pip install playwright && playwright install` | `playwright --version` |
| Linter | ruff | 0.6+ | `pip install ruff` | `ruff --version` |
| VCS | git | 2.x | `brew install git` | `git --version` |
| Build | make | 4+ | (bundled) | `make --version` |
| IaC | aws-cdk-lib | 2.x | `pip install aws-cdk-lib` | `cdk --version` |
| Frontend | Bootstrap | 5.3+ | CDN | — |
| Graph UI | Cytoscape.js | 3.28+ | CDN/npm | — |

---

## Skill Coverage Report

| Domain | Covered Skills | Gaps |
|--------|---------------|------|
| Application Blocks | Django Backend Patterns (#10) | Graph-over-ORM pattern — custom |
| Integration & API | — | FastMCP thin-client pattern — custom |
| Code Organization | Django patterns | — |
| Data Architecture | — | Bitemporal graph — custom |
| Test Strategy | pytest (#13), Playwright (#12) | — |
| Infrastructure | AWS CDK (#22), EB Blue/Green (#43) | — |
| CI/CD | GitHub Actions (#21) | — |
| Frontend | Django HTMX (#11), Bootstrap (#44) | Cytoscape integration — custom |

---

## Key Decisions with Rationale

| # | Domain | Decision | Rationale |
|---|--------|----------|-----------|
| 1 | Data | Graph-over-Django ORM | Team expertise, EB simplicity, no Neo4j ops |
| 2 | Data | Bitemporal append-only | Time-travel + diff without event sourcing complexity |
| 3 | API | DRF as engine | Single behavior surface for all clients |
| 4 | Integration | Ratatosk HTTP-only package | Runs local, CI, or Lambda unchanged |
| 5 | LLM | ABC provider seam | Qwen local dev, Anthropic production |
| 6 | Infra | Elastic Beanstalk | Small team, managed platform |
| 7 | CI/CD | Release-gated | Huginn semver control |

---

## Discovered Patterns & Lessons Learned

_Reserved — populated during implementation._
