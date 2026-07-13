# CI/CD Requirements

## Trigger Model
**Chosen**: Release-gated (Huginn model)  
**Rationale**: Explicit semver control for production deploys

```bash
gh release create vX.Y.Z  # production deploy trigger
```

## Pipeline Architecture

```
gh release create vX.Y.Z
  → test (pytest)
  → build (ECR push)
  → deploy-idle (EB deploy → idle smoke)
  → manual approval
  → make swap (CNAME promote)
  → prod smoke (/health/ revision)
```

## Make Targets
| Target | Description |
|--------|-------------|
| `make test` | pytest |
| `make lint` | ruff check |
| `make build` | Docker build + ECR push |
| `make deploy-idle` | Deploy to idle EB env |
| `make swap` | EB CNAME promote |
| `make eb-status` | Show EB environments |

## GitHub Workflows
| File | Trigger | Purpose |
|------|---------|---------|
| `.github/workflows/build-and-deploy.yml` | release | test + build + deploy-idle |
| `.github/workflows/promote.yml` | workflow_dispatch | CNAME swap |

## Quality Gates
| Gate | Criteria |
|------|----------|
| Test | All pytest pass |
| Idle smoke | HTTP 200 on `/health/` |
| Prod smoke | HTTPS 200, revision match |

## Secrets
| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | ECR, EB deploy |
| `DATABASE_URL` | EB environment (from CDK) |
