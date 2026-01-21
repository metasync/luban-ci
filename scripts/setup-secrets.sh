#!/usr/bin/env bash
set -e

# Load secrets
if [ -f secrets/quay.env ]; then
    source secrets/quay.env
fi
if [ -f secrets/github.env ]; then
    source secrets/github.env
fi

# Create Namespace if not exists
kubectl create ns luban-ci --dry-run=client -o yaml | kubectl apply -f -

# Quay Credentials (for pushing images)
kubectl delete secret quay-creds -n luban-ci --ignore-not-found
kubectl create secret docker-registry quay-creds \
    -n luban-ci \
    --docker-server=quay.io \
    --docker-username="$QUAY_USERNAME" \
    --docker-password="$QUAY_PASSWORD" \
    --docker-email="ci@luban.com"

# GitHub Credentials (for cloning/pushing code)
kubectl delete secret github-creds -n luban-ci --ignore-not-found
kubectl create secret generic github-creds \
    -n luban-ci \
    --from-literal=username="$GITHUB_USERNAME" \
    --from-literal=token="$GITHUB_TOKEN"

echo "Secrets created in namespace 'luban-ci'."
