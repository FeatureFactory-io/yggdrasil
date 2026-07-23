# Repository fixtures for Ratatosk discovery

| Path | Purpose |
|------|---------|
| `sample_webapp/` | Minimum-minimum Python/FastAPI fixture for `ratatosk bootstrap` (ACT-1-DISC-*, ACT-1-LLM-*) |
| `sample_stdin/` | Diff and prose blobs for `ratatosk update` (ACT-6-CICD-*) |
| `empty_repo/` | Empty tree after ignores (ACT-1-DISC-12); only `.gitkeep` |

## sample_webapp

Multi-container order/payment domain with four C4 elements (see `expected_elements.yaml`):

- **Containers:** Payment API, Order Service
- **Components:** Order Domain, Billing Worker

Stack signals: FastAPI, Uvicorn, SQLAlchemy, PostgreSQL 16 (`docker-compose.yml`, `Dockerfile`).

Used by bootstrap MVP-W1 scenarios; fixture app need not run in CI.
