#!/usr/bin/env bash
# Deploy backend container to Elastic Beanstalk staging environment.
# Mirrors Huginn's deploy-staging.sh pattern.
set -euo pipefail

APP_NAME="${EB_APP_NAME:-yggdrasil}"
ENV_NAME="${EB_STAGING_ENV:-yggdrasil-staging}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo "[deploy-staging] Building Docker image..."
docker build -t "${APP_NAME}:latest" .

echo "[deploy-staging] Pushing to ECR..."
# aws ecr get-login-password ... | docker login ...
# docker tag / push — fill in ECR repo URI in CI

echo "[deploy-staging] Deploying to EB environment: ${ENV_NAME}"
# eb deploy "${ENV_NAME}" --region "${REGION}"

echo "[deploy-staging] Done. Visit: https://${ENV_NAME}.${REGION}.elasticbeanstalk.com/health/"
