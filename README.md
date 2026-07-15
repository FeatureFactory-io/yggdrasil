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
| MCP facade container | GHCR (public) | Run locally, point any MCP client at it |
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

### 4. Run tests

```bash
make test               # unit + integration tests (no Docker required)
make test-at            # acceptance tests (behave-django)
make test-all           # everything
```

---

## MCP usage

### Option A — local Docker container (recommended)

The MCP client starts the container on demand. No port mapping or manual `docker run` needed.

`mcp_config.json`:

```json
{
  "mcpServers": {
    "yggdrasil": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "YGGDRASIL_TOKEN=<your-token>",
        "-e", "YGGDRASIL_SERVER_URL=https://yggdrasil.featurefactory.io",
        "ghcr.io/yggdrasil/yggdrasil-mcp:latest"
      ]
    }
  }
}
```

The container authenticates against the Yggdrasil DRF API using `YGGDRASIL_TOKEN` and communicates with the MCP client over stdio. Your token never leaves your machine.

### Option B — MCP direct (cloud, SSE)

```json
{
  "mcpServers": {
    "yggdrasil": {
      "url": "https://yggdrasil.featurefactory.io/mcp/sse",
      "headers": { "Authorization": "Bearer <your-token>" }
    }
  }
}
```

---

## Ratatosk CLI

```bash
pip install ratatosk

# Bootstrap a repository into the knowledge graph:
ratatosk bootstrap ./my-repo --token=<your-token>

# Use token from environment (CI/CD):
export YGGDRASIL_TOKEN=<your-token>
ratatosk bootstrap ./my-repo
```

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
├── features/               # BDD feature files (behave)
│   ├── at/                 # Acceptance tests — single-page/feature scope
│   └── e2e/                # E2E tests — full user journey scope (Playwright)
├── scripts/                # deploy-staging.sh, promote-prod.sh
├── logs/                   # app.log, gui.log, consumption.log (gitignored)
├── docker-compose.yml      # Local: db + redis + web + worker + mcp (+ ollama)
├── Dockerfile              # Backend container (ECR → EB)
├── Dockerfile.mcp          # MCP facade container (GHCR)
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
