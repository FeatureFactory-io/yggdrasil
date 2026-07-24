# Yggdrasil

AI-augmented architecture knowledge-graph platform. Keep a living, queryable model of your software system in sync with its codebase via CI/CD.

Query through a **web GUI**, a **REST API**, and an **MCP interface** usable from any AI client (Cursor, Claude Desktop, Ratatosk CLI).

---

## Architecture overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients                                                        │
│  Browser (HTMX)  ·  Ratatosk CLI  ·  MCP facade  ·  AI agents │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────────────┐
│  Django modular monolith  (Elastic Beanstalk, blue/green)       │
│  auth · graph · changeset · munin · ratatosk · mcp · api · web │
└──────────┬──────────────────────┬───────────────────────────────┘
           │                      │
    ┌──────▼──────┐       ┌───────▼──────┐
    │  PostgreSQL │       │  Redis       │
    │  (Aurora)   │       │  (Celery +   │
    └─────────────┘       │   cache)     │
                          └──────────────┘
```

Three distributable artifacts per release:

| Artifact | Distribution | Purpose |
|---|---|---|
| Backend container | ECR → Elastic Beanstalk | Django web app + REST API |
| MCP facade container | Planned (`Dockerfile.mcp`) | Case B httpx→API image — **not released yet** |
| Ratatosk CLI | PyPI + GitHub Releases | CI/CD field agent |

---

## Quick start — local desktop mode

### Prerequisites

| Tool | Minimum | Install (macOS) |
|---|---|---|
| Python | 3.14 | `brew install python@3.14` |
| uv | 0.4+ | `brew install uv` |
| Docker | 24+ | `brew install --cask docker` |
| make | 4+ | bundled on macOS |
| git | 2.x | bundled on macOS |

### 1. Provision

```bash
git clone https://github.com/yggdrasil/yggdrasil.git
cd yggdrasil
make provision          # creates .venv, installs deps, copies .env, installs pre-commit hooks
```

Edit `.env` if needed (defaults work for local Docker setup).

### 2. Start backing services

```bash
make up                 # starts Postgres + Redis in Docker

# Optional — offline/desktop mode with local LLM:
make up-desktop         # also starts Ollama (set LLM_PROVIDER=ollama in .env)
```

### 3. Migrate and run

```bash
make migrate            # apply DB migrations
make run                # Django dev server → http://localhost:8000
```

Health check: `curl http://localhost:8000/health/` → `{"status": "ok"}`

**Optional — Celery worker** (async Munin/plan jobs):

```bash
make worker             # separate terminal; requires make up (Redis)
```

**Optional — local LLM (Ollama)** for Ratatosk bootstrap without cloud API keys:

```bash
make up-desktop         # Postgres + Redis + Ollama
# In .env: LLM_PROVIDER=ollama, OLLAMA_BASE_URL=http://localhost:11434
```

In Cursor/VS Code you can also use **F5** (`.vscode/launch.json` → Django runserver). Requires `.env` and `make up`.

### 4. Create an API token

Ratatosk and MCP call the server with a **personal access token** (PAT):

1. Open http://localhost:8000 and sign in (or `make createsuperuser` first).
2. Go to **Auth → Tokens** (`/auth/tokens/`) and create a **read-write** token.
3. Copy the raw token once (it is not shown again).

```bash
export YGGDRASIL_TOKEN=<paste-token-here>
```

`.env` already sets `YGGDRASIL_SERVER_URL=http://localhost:8000` for local dev.

### 5. Run Ratatosk (bootstrap a repo)

See **[Ratatosk CLI](#ratatosk-cli)** for full commands, flags, config, and CI examples. Minimal local bootstrap:

```bash
export YGGDRASIL_TOKEN=<token>
uv run python -m ratatosk.cli bootstrap ./tests/fixtures/repos/sample_webapp \
  --model yggdrasil --metamodel c4 --server http://localhost:8000
```

### 6. Run tests

```bash
make test               # unit + integration tests (no Docker required)
make test-at            # acceptance tests (behave-django)
make test-all           # everything
```

---

## Ratatosk CLI

Ratatosk scans a repository (or stdin) and proposes graph changes via the Yggdrasil MCP HTTP bridge (`POST /mcp/tools/<name>/`). It does **not** import Django — it is a remote client only.

### Install

```bash
# From PyPI (any machine)
pip install ratatosk

# From this monorepo (development)
uv run python -m ratatosk.cli --help
```

### Prerequisites

| Requirement | Local dev | Production / CI |
|---|---|---|
| Yggdrasil server | `make run` → `:8000` | `https://yggdrasil.featurefactory.io` |
| Personal access token | Create at `/auth/tokens/` | Same (read-write for bootstrap) |
| LLM for discovery | `LLM_PROVIDER=ollama` + `make up-desktop`, or set `ANTHROPIC_API_KEY` | Cloud API key in env |

```bash
export YGGDRASIL_TOKEN=<pat>                          # or --token on each command
export YGGDRASIL_SERVER_URL=http://localhost:8000     # default in .env for local dev
export LLM_PROVIDER=ollama                            # or anthropic
export OLLAMA_BASE_URL=http://localhost:11434         # when using local Ollama
```

Logs: `logs/ratatosk.log` (truncated each run). Override with `RATATOSK_LOG_LEVEL=DEBUG` or `RATATOSK_LOG_FILE=/path/to.log`.

### Commands

```bash
ratatosk --help              # global options
ratatosk --version
ratatosk bootstrap --help
ratatosk update --help
```

| Command | Purpose |
|---|---|
| `bootstrap PATH` | Scan a repo on disk; propose initial architecture elements |
| `update` | Read **stdin** (git diff, notes); propose a delta ChangeSet (does not wipe the model) |

### `bootstrap` — flags

```bash
ratatosk bootstrap <path> \
  --model <slug> \
  [--token <pat>] \
  [--server <url>] \
  [--metamodel c4] \
  [--instructions "..."] \
  [--exclude <glob>] ...
```

| Flag | Env var | Default | Description |
|---|---|---|---|
| `PATH` | — | — | Repository root to scan (required positional) |
| `--model` | — | — | Target model slug (required), e.g. `yggdrasil` |
| `--token` | `YGGDRASIL_TOKEN` | — | Personal access token (required unless env is set) |
| `--server` | `YGGDRASIL_SERVER_URL` | `https://yggdrasil.featurefactory.io` | Yggdrasil base URL |
| `--metamodel` | `RATATOSK_METAMODEL` | `c4` | Metamodel profile bound to the model |
| `--instructions` | — | — | Extra LLM steering text for this run |
| `--exclude` | `RATATOSK_EXCLUDE` | — | Path prefix or glob to skip (repeatable or comma-separated) |

**Examples**

```bash
# Local dev (from yggdrasil clone — server must be running)
uv run python -m ratatosk.cli bootstrap ./my-repo \
  --model yggdrasil \
  --metamodel c4 \
  --server http://localhost:8000

# Production
export YGGDRASIL_SERVER_URL=https://yggdrasil.featurefactory.io
ratatosk bootstrap ./my-repo --model yggdrasil --server "$YGGDRASIL_SERVER_URL"

# Skip paths and steer the scout
ratatosk bootstrap ./my-repo --model yggdrasil \
  --exclude node_modules --exclude "**/migrations/**" \
  --instructions "Focus on public HTTP APIs only."

# Explicit token (CI)
ratatosk bootstrap "$CI_PROJECT_DIR" \
  --token "$YGGDRASIL_TOKEN" \
  --model yggdrasil \
  --server "$YGGDRASIL_SERVER_URL"
```

### `update` — flags

Reads stdin only (pipe or redirect). Exits with an error if stdin is a TTY.

```bash
git log -p v1.0..HEAD | ratatosk update \
  --model <slug> \
  [--token <pat>] \
  [--server <url>] \
  [--metamodel c4] \
  [--instructions "..."]
```

| Flag | Env var | Default | Description |
|---|---|---|---|
| `--model` | — | — | Target model slug (required) |
| `--token` | `YGGDRASIL_TOKEN` | — | Personal access token |
| `--server` | `YGGDRASIL_SERVER_URL` | `https://yggdrasil.featurefactory.io` | Yggdrasil base URL |
| `--metamodel` | `RATATOSK_METAMODEL` | `c4` | Metamodel profile |
| `--instructions` | — | — | Extra LLM steering text for this run |

**Examples**

```bash
# Incremental update from recent commits
git log -p HEAD~1..HEAD | ratatosk update --model yggdrasil --metamodel c4

# Single commit
git show abc1234 --format= --patch | ratatosk update --model yggdrasil

# CI on merge
git log -p "$CI_COMMIT_BEFORE_SHA..$CI_COMMIT_SHA" | \
  ratatosk update --model yggdrasil --token "$YGGDRASIL_TOKEN"
```

### Configuration (env + YAML)

CLI flags override env; env overrides repo/home YAML for the same key.

**Repo YAML** (optional) — `ratatosk.yaml` or `.ratatosk/config.yaml` in the repo root:

```yaml
llm_provider: ollama
base_model: qwen3:14b
planning_model: sonnet5
ollama_base_url: http://localhost:11434
max_extract_targets: 50
max_file_reads_per_run: 1000
exclude:
  - node_modules/**
  - "**/tests/**"
instructions: "Prefer C4 containers over classes."
```

**Home YAML** (optional) — `~/.ratatosk/config.yaml` (same keys; repo file wins on conflict).

**Environment variables** (discovery / LLM — not all have CLI flags):

| Variable | Purpose |
|---|---|
| `YGGDRASIL_TOKEN` | PAT for MCP HTTP calls |
| `YGGDRASIL_SERVER_URL` | Server base URL |
| `LLM_PROVIDER` | `ollama` \| `anthropic` \| `openai` |
| `BASE_MODEL` | Model alias or id (`haiku`, `sonnet5`, `qwen3:14b`, …) |
| `RATATOSK_PLANNING_MODEL` | Planning-tier model for project map (default `sonnet5`) |
| `RATATOSK_MAX_EXTRACT_TARGETS` | Scout path budget (default `50`) |
| `RATATOSK_MAX_FILE_READS_PER_RUN` | Hard cap on file reads per run (default `1000`) |
| `RATATOSK_METAMODEL` | Default metamodel when `--metamodel` omitted |
| `RATATOSK_EXCLUDE` | Comma-separated exclude patterns |
| `OLLAMA_BASE_URL` | Ollama endpoint when `LLM_PROVIDER=ollama` |
| `ANTHROPIC_API_KEY` | Required when `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | Required when `LLM_PROVIDER=openai` |

After bootstrap/update, review the proposed ChangeSet in the Yggdrasil GUI (`/changesets/`) and approve or reject.

---

## MCP usage (local dev)

Two paths — **IDE MCP** (stdio) and **Ratatosk CLI** (HTTP on the Django app).

| Client | Process | Requires |
|--------|---------|----------|
| Cursor / Claude Desktop | `mcp_server --transport stdio` | `make up`, `make migrate`, `YGGDRASIL_TOKEN` in MCP env |
| Ratatosk CLI | Django `make run` on `:8000` | same token; `--server=http://localhost:8000` |

### Cursor (stdio) — current setup

In **Cursor → MCP → yggdrasil**, use a single command (replace path with your clone):

```bash
uv run --directory /path/to/yggdrasil python manage.py mcp_server --transport stdio
```

Set **`YGGDRASIL_TOKEN`** in the MCP server environment (Cursor MCP settings → env). The server binds the token owner on startup (`manage.py mcp_server` reads `YGGDRASIL_TOKEN` from the environment).

Does **not** require `make run` — MCP talks to Django/ORM directly. Does require Postgres/Redis up (`make up`) and migrations applied (`make migrate`).

Equivalent JSON (if your client splits command/args):

```json
{
  "mcpServers": {
    "yggdrasil": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/yggdrasil",
        "python", "manage.py", "mcp_server", "--transport", "stdio"
      ],
      "env": {
        "YGGDRASIL_TOKEN": "<your-token>"
      }
    }
  }
}
```

### Ratatosk CLI (HTTP bridge)

With `make run` listening on port 8000, Ratatosk calls `POST /mcp/tools/<name>/` automatically when `--server=http://localhost:8000` (default in `.env` as `YGGDRASIL_SERVER_URL`).

```bash
curl -s -X POST http://localhost:8000/mcp/tools/list_elements/ \
  -H "Authorization: Bearer $YGGDRASIL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"model": "yggdrasil", "limit": 10}}'
```

### Optional — MCP HTTP on port 8001

Separate from Django `:8000` and from stdio:

```bash
uv run --directory /path/to/yggdrasil python manage.py mcp_server --transport http --port 8001
```

---

## MCP usage (remote server)

**What exists today:** MCP tools run **inside the Django app** (Case A). Ratatosk and scripts call them over HTTP on the same host as the web app — not via a separate published Docker MCP image.

### Ratatosk / scripts against production

See [Ratatosk CLI](#ratatosk-cli) for all flags. Minimal example:

```bash
export YGGDRASIL_SERVER_URL=https://yggdrasil.featurefactory.io
export YGGDRASIL_TOKEN=<your-pat>
ratatosk bootstrap /path/to/repo --model yggdrasil --server "$YGGDRASIL_SERVER_URL"
```

Each tool is `POST /mcp/tools/<name>/` with `Authorization: Bearer <token>` (same contract as local `make run` on `:8000`).

### Cursor / Claude Desktop against a remote server

**Not supported yet.** IDE clients need **local stdio** (see [MCP usage (local dev)](#mcp-usage-local-dev)): `manage.py mcp_server --transport stdio` against a local DB with `make up` + `make migrate`.

There is **no** `/mcp/sse` URL on production — do **not** point Cursor at `"url": "https://yggdrasil.featurefactory.io/mcp/sse"`. There is also **no** published `featurefactory-io/yggdrasil-mcp` Docker image yet (`Dockerfile.mcp` is scaffold-only). Until Case B ships, remote access is Ratatosk/scripts via `POST /mcp/tools/<name>/` only.

---

## Common commands

| Goal | Command |
|------|---------|
| First-time setup | `make provision` |
| Start DB + Redis | `make up` |
| Start DB + Redis + Ollama | `make up-desktop` |
| Apply migrations | `make migrate` |
| Web app | `make run` → http://localhost:8000 |
| MCP (Cursor stdio) | `uv run --directory . python manage.py mcp_server --transport stdio` |
| Celery worker | `make worker` |
| Bootstrap repo (dev) | See [Ratatosk CLI](#ratatosk-cli) |
| All tests | `make test-all` |
| Lint + types | `make check` |
| Stop Docker | `make down` |

Run `make help` for the full Makefile target list.

---

## Project structure

```
yggdrasil/
├── src/yggdrasil/          # Django project (installed as package)
│   ├── auth/               # Session auth, personal access tokens, RBAC
│   ├── graph/              # Element, Relationship, Stereotype, Package, Diagram
│   ├── changeset/          # ChangeSet, ChangeSetItem — all writes go through here
│   ├── munin/              # Agentic planner (larger LLM)
│   ├── ratatosk/           # RataskRun model, CLI integration models
│   ├── mcp/                # FastMCP server exposing the service layer
│   ├── api/                # DRF routers and serializers
│   ├── llm/                # LLMClient protocol + Anthropic/OpenAI/Ollama adapters
│   └── web/                # Django views, HTMX partials, templates, Cytoscape.js
├── ratatosk/               # Ratatosk CLI package (published to PyPI)
├── infra/                  # AWS CDK stacks (Python)
├── docs/
│   └── features/           # BDD spec + AT runner (behave)
│       ├── act-*/          # .feature files per act (@wip until implemented)
│       ├── steps/          # Step Library
│       └── environment.py
├── tests/
│   └── e2e/                # E2E journey tests (Playwright)
├── scripts/                # deploy-staging.sh, promote-prod.sh
├── logs/                   # app.log, gui.log, consumption.log (gitignored)
├── docker-compose.yml      # Local: db + redis + web + worker + mcp (+ ollama)
├── Dockerfile              # Backend container (ECR → EB)
├── Dockerfile.mcp          # Planned Case B MCP facade (scaffold — not released)
├── Makefile                # All dev operations: provision/run/test/lint/staging/swap
└── pyproject.toml          # Python deps (uv), ruff, mypy, pytest, commitizen
```

---

## Development workflow

```bash
make lint               # ruff check
make format             # ruff format
make typecheck          # mypy
make check              # lint + typecheck

make audit              # pip-audit dependency vulnerability scan
```

Commit convention: [Conventional Commits](https://www.conventionalcommits.org/) enforced via `commitizen` pre-commit hook.

```
feat(graph): add Element create endpoint
fix(auth): handle expired token gracefully
docs(readme): update quick start
```

---

## Deployment

### Staging

```bash
make staging            # build + push to ECR, deploy to EB staging
```

### Production (blue/green swap)

```bash
make swap               # CNAME swap: staging ↔ production (zero-downtime)
```

CloudFront origin points to the fixed production CNAME. The CNAME swap reassigns which underlying EB environment responds — zero downtime, instant rollback by swapping back.

---

## Architecture decision record

All architectural decisions are documented in [`docs/architecture/SAO.md`](docs/architecture/SAO.md).

Key decisions at a glance:

| Decision | Choice | Why |
|---|---|---|
| Architecture | Modular monolith | Team size; bounded contexts give clear growth path |
| Rendering | Server-rendered + HTMX | Testability; avoids SPA complexity |
| LLM abstraction | `LLMClient` protocol | Swap Ollama ↔ Anthropic ↔ OpenAI per environment |
| Async broker | Redis (not SQS) | Dev/prod parity; works offline; doubles as cache |
| Infrastructure | AWS EB + Aurora | Proven pattern; blue/green at zero cost; PITR for RPO |
| Test strategy | Test Trophy (pytest + behave + Playwright) | Integration confidence > unit coverage |

---

## Licence

Proprietary — all rights reserved.
