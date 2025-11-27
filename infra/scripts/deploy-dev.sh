#!/usr/bin/env bash
set -euo pipefail

APP_NAME="rag-app"
AWS_REGION="${AWS_REGION:-eu-north-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query 'Account' --output text)}"
ECR_REPO_NAME="rag-app-repo"
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

IMAGE_TAG="$(date -u +'%Y%m%d-%H%M%S')"
docker build -t "${APP_NAME}:${IMAGE_TAG}" .

aws ecr get-login-password --region "${AWS_REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker tag "${APP_NAME}:${IMAGE_TAG}" "${ECR_REPO}:${IMAGE_TAG}"
docker push "${ECR_REPO}:${IMAGE_TAG}"

cd infra/terraform
terraform apply -auto-approve \
  -var="container_image_tag=${IMAGE_TAG}" \
  -var="desired_count=1"
