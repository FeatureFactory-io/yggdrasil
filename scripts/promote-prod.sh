#!/usr/bin/env bash
# Blue/green CNAME swap: promote staging → production.
# CloudFront origin points to the production CNAME; this swap
# reassigns which underlying EB environment answers that CNAME.
set -euo pipefail

APP_NAME="${EB_APP_NAME:-yggdrasil}"
SOURCE_ENV="${EB_STAGING_ENV:-yggdrasil-staging}"
DEST_ENV="${EB_PROD_ENV:-yggdrasil-prod}"
REGION="${AWS_DEFAULT_REGION:-us-east-1}"

echo "[promote-prod] Swapping CNAMEs: ${SOURCE_ENV} ↔ ${DEST_ENV}"
aws elasticbeanstalk swap-environment-cnames \
  --source-environment-name "${SOURCE_ENV}" \
  --destination-environment-name "${DEST_ENV}" \
  --region "${REGION}"

echo "[promote-prod] Swap complete. Production is now running staging build."
echo "[promote-prod] Health: https://yggdrasil.featurefactory.io/health/"
