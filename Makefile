.DEFAULT_GOAL := help
SHELL := /bin/bash

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
UV       := uv
PYTHON   := $(UV) run python
MANAGE   := $(PYTHON) manage.py
COMPOSE  := docker compose
APP      := yggdrasil
PYTHONPATH := src

export PYTHONPATH

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
.PHONY: help
help:   ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
.PHONY: install
install:  ## Install all deps (including dev) into .venv
	$(UV) sync --group dev

.PHONY: hooks
hooks:  ## Install pre-commit hooks
	$(UV) run pre-commit install --hook-type pre-commit --hook-type commit-msg

.PHONY: provision
provision: install hooks  ## Full local setup: install deps + hooks + copy .env
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; fi
	@echo "✓ provision complete — edit .env then: make up && make migrate && make run"

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
.PHONY: up
up:   ## Start backing services (db, redis) in background
	$(COMPOSE) up -d db redis

.PHONY: up-desktop
up-desktop:  ## Start all services including Ollama (desktop / offline mode)
	$(COMPOSE) --profile desktop up -d

.PHONY: down
down:  ## Stop all Docker services
	$(COMPOSE) down

.PHONY: logs
logs:  ## Tail Docker service logs
	$(COMPOSE) logs -f

# ---------------------------------------------------------------------------
# Django
# ---------------------------------------------------------------------------
.PHONY: run
run:  ## Run Django dev server (requires: make up)
	$(MANAGE) runserver

.PHONY: migrate
migrate:  ## Apply database migrations
	$(MANAGE) migrate

.PHONY: makemigrations
makemigrations:  ## Generate new migrations
	$(MANAGE) makemigrations

.PHONY: shell
shell:  ## Open Django shell
	$(MANAGE) shell_plus

.PHONY: createsuperuser
createsuperuser:  ## Create a Django admin superuser
	$(MANAGE) createsuperuser

.PHONY: collectstatic
collectstatic:  ## Collect static files
	$(MANAGE) collectstatic --noinput

.PHONY: seed
seed:  ## Load development seed data
	$(MANAGE) loaddata fixtures/seed.json

# ---------------------------------------------------------------------------
# Workers
# ---------------------------------------------------------------------------
.PHONY: worker
worker:  ## Start Celery worker
	$(UV) run celery -A $(APP) worker --loglevel=info

.PHONY: beat
beat:  ## Start Celery beat scheduler
	$(UV) run celery -A $(APP) beat --loglevel=info

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
.PHONY: test
test:  ## Run unit + integration tests with coverage
	$(UV) run pytest --cov=src --cov-report=term-missing -q

.PHONY: test-unit
test-unit:  ## Run unit tests only
	$(UV) run pytest -m unit -q

.PHONY: test-integration
test-integration:  ## Run integration tests (requires DB)
	$(UV) run pytest -m integration -q

.PHONY: test-at
test-at:  ## Run acceptance tests (behave-django, --simple: Django test client, atomic per-scenario rollback)
	DJANGO_SETTINGS_MODULE=yggdrasil.test_settings $(MANAGE) behave --simple features/at/

.PHONY: test-e2e
test-e2e:  ## Run E2E tests (behave-django + Playwright, live server required)
	DJANGO_SETTINGS_MODULE=yggdrasil.test_settings $(MANAGE) behave features/e2e/

.PHONY: test-all
test-all: test test-at  ## Run all tests (unit, integration, AT)

.PHONY: watch
watch:  ## Run tests continuously on file changes (unit + integration)
	$(UV) run python continuous_test_runner.py

# ---------------------------------------------------------------------------
# Linting & formatting
# ---------------------------------------------------------------------------
.PHONY: lint
lint:  ## Lint with ruff
	$(UV) run ruff check src/ ratatosk/

.PHONY: format
format:  ## Format with ruff
	$(UV) run ruff format src/ ratatosk/

.PHONY: typecheck
typecheck:  ## Type-check with mypy
	$(UV) run mypy src/

.PHONY: audit
audit:  ## Check for dependency vulnerabilities
	$(UV) run pip-audit

.PHONY: check
check: lint typecheck  ## Run lint + typecheck

# ---------------------------------------------------------------------------
# Release (mirrors Huginn pattern)
# ---------------------------------------------------------------------------
.PHONY: bump
bump:  ## Bump version and update CHANGELOG (commitizen)
	$(UV) run cz bump --changelog

.PHONY: staging
staging:  ## Deploy to staging Elastic Beanstalk environment
	bash scripts/deploy-staging.sh

.PHONY: swap
swap:  ## Blue/green CNAME swap — promote staging → production
	bash scripts/promote-prod.sh

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------
.PHONY: clean
clean:  ## Remove build artefacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov coverage.xml dist/ build/ *.egg-info/
