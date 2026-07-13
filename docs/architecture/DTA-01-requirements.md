# DTA-01: ESM Capability Requirements per Domain

Extracted from ESM artifacts for Yggdrasil.

## Domain: Application Blocks (DTA-02)
- Bounded contexts: `graph`, `api`, `mcp`, `web`, `core`, `ratatosk` (pip package)
- UI: server-rendered HTMX + Cytoscape graph + AI chat
- Pattern: modular monolith

## Domain: Integration & API (DTA-03)
- DRF REST as engine; traversal/filter endpoints; semantic URLs
- FastMCP thin client; Ratatosk CLI HTTP client
- No external 3rd-party integrations in MVP

## Domain: Code Organization (DTA-04)
- Monorepo: `yggdrasil/` Django project + `ratatosk/` package at repo root
- Layers: models → services → serializers/views

## Domain: Data Architecture (DTA-05)
- Graph-over-Django: Element, Relationship, Stereotype, Package, Diagram
- JSONB properties; bitemporal valid_from/valid_to/recorded_at
- Recursive CTE traversal; Apache AGE escape hatch

## Domain: Test Strategy (DTA-06)
- pytest + DRF APIClient; Playwright for HTMX E2E
- Test trophy: many unit, some integration, few E2E

## Domain: Performance (DTA-07)
- GIN indexes on JSONB; pagination default 50; optional Redis cache later

## Domain: Error Handling (DTA-08)
- DRF standardized errors; stereotype validation on write; ChangeSet rollback

## Domain: Infrastructure (DTA-09)
- AWS EB + RDS Postgres + VPC; us-east-1 default

## Domain: CI/CD (DTA-10)
- Release-gated GitHub Actions; test → build → deploy-idle → smoke → promote

## Domain: Release & Rollback (DTA-11)
- EB blue/green CNAME swap

## Domain: Observability (DTA-12)
- Three-tier: app logs, GUI interaction logs, LLM token logs → CloudWatch

## Domain: Config & Secrets (DTA-13)
- django-environ; LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY

## Domain: Security (DTA-14)
- Django auth + Groups; Stereotype×Group CRUDL matrix; PBAC property filters

## Domain: Backup & Recovery (DTA-15)
- RDS automated backups 7-day retention; bitemporal aids point-in-time graph

## Domain: Developer Experience (DTA-16)
- Makefile; ruff; pre-commit; local Qwen via OpenAI-compatible endpoint

## Domain: Documentation (DTA-17)
- docs/ layout; SAO living doc; drf-spectacular OpenAPI
