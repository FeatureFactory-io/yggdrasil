# Infrastructure Requirements

## AWS Region
us-east-1

## Deployment Style
**Chosen**: Elastic Beanstalk  
**Rationale**: Single Django application, small team, managed infrastructure  
**Skill Reference**: AWS Elastic Beanstalk Blue/Green Deployment (#43)

## Repo Layout
- [x] `infra/` in application monorepo

## Services Required
| Service | Purpose | Configuration |
|---------|---------|---------------|
| VPC | Network isolation | 2 public + 2 private subnets, NAT GW |
| Elastic Beanstalk | Managed Docker | 2 envs: `yggdrasil-prod`, `yggdrasil-idle` |
| ECR | Container registry | 1 repo: `yggdrasil-web` |
| RDS | PostgreSQL 16 | db.t4g.micro, private subnet |
| S3 | DB backups | `yggdrasil-db-backups-{account}` |
| Route53 | DNS | CNAME → EB prod environment |

## Blue/Green Strategy
- Two EB environments; CNAME swap via `swap-environment-cnames`
- Deploy always to idle environment first

## Environment Variables
| Var | Example |
|-----|---------|
| `EB_APP` | `yggdrasil` |
| `EB_ENV_A` | `yggdrasil-prod` |
| `EB_ENV_B` | `yggdrasil-idle` |

## Cost Estimate
~$70–100/month (2 EB + RDS micro + NAT)

## Security Requirements
- RDS in private subnets; EB instances in private subnets
- Security groups: ALB ↔ EB ↔ RDS
- IAM: EB service role, instance profile (ECR, S3, SSM)
