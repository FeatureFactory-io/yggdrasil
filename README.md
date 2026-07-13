# Yggdrasil

AI-maintained organizational knowledge repository.

## Quickstart

```bash
make setup    # venv + deps + migrate
make run      # http://localhost:8000
make test
```

## Docs

- [PRD.MD](PRD.MD) — product requirements
- [docs/architecture/SAO.md](docs/architecture/SAO.md) — system architecture
- [docs/features/user_journey.md](docs/features/user_journey.md) — UX journey

## Ratatosk CLI

```bash
pip install -e ./ratatosk
ratatosk scan-gitlab --project mygroup/myservice --api-url http://localhost:8000
```

## MCP

```bash
python mcp_server/server.py
```
