# Software Process (DSP)

## Branching
- `main` — production-ready
- Feature branches: `feat/issue-description`

## Definition of Done
- [ ] Tests pass (`make test`)
- [ ] Lint clean (`make lint`)
- [ ] Screen ID traceability maintained
- [ ] Conventional commit message

## AI IDE
- Target: Cursor
- Config: `AGENTS.md`, `.cursor/playbooks/edda/`

## Tooling
- ruff (format + lint)
- pytest + pytest-django
- pre-commit hooks
