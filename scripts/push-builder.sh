#!/usr/bin/env bash
set -e

if [ ! -f secrets/quay.env ]; then
    echo "secrets/quay.env not found!"
    exit 1
fi
source secrets/quay.env

echo "Logging in to Quay.io..."
echo "$QUAY_PASSWORD" | docker login -u "$QUAY_USERNAME" --password-stdin quay.io

BUILDER_TAG="quay.io/$QUAY_USERNAME/luban-builder:latest"
echo "Tagging builder as $BUILDER_TAG"
docker tag luban-ci/builder:latest "$BUILDER_TAG"

echo "Pushing builder..."
docker push "$BUILDER_TAG"
echo "Builder pushed successfully."
