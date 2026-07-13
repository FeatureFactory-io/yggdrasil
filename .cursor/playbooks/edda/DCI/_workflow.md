# Design & Deploy Cloud Infra

**Playbook**: Edda v43.0 (Released)
**Workflow ID**: 12
**Abbreviation**: DCI
**Description**: Design and deploy cloud infrastructure using AWS CDK with Python. Supports two deployment styles chosen in DCI-01: **Kubernetes/EKS** (separate infra repo, weighted Route53) or **Elastic Beanstalk** (monorepo or separate repo, EB CNAME swap). Establish Makefile targets for infra operations and GitHub Actions for CDK deploy. Blue/green switching is style-specific: Route53 weights (EKS) or EB swap-environment-cnames (EB).
**Total Activities**: 7
**Export Date**: 2026-07-06 10:18 UTC

## Activities

See individual activity files in this directory.
