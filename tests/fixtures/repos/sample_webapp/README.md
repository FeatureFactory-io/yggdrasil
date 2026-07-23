# Sample Webapp

Architecture overview for Ratatosk discovery tests.

## Stack

- Python 3.12+
- FastAPI + Uvicorn (HTTP containers)
- SQLAlchemy (persistence layer — stub)
- PostgreSQL 16 (`docker-compose.yml`)

## Containers

- **Payment API** — HTTP container exposing payment endpoints (`src/payment_api/app.py`)
- **Order Service** — web container for order intake (`src/order_service/app.py`)

## Components

- **Order Domain** — domain logic for orders (`src/order_domain/service.py`)
- **Billing Worker** — background billing component (`src/billing_worker/worker.py`)

## Path map (C4 → source)

| Element | Stereotype | Path |
|---------|------------|------|
| Payment API | Container | `src/payment_api/app.py` |
| Order Service | Container | `src/order_service/app.py` |
| Order Domain | Component | `src/order_domain/service.py` |
| Billing Worker | Component | `src/billing_worker/worker.py` |

Order Service imports Order Domain for order placement. Billing Worker is a standalone background component stub.
