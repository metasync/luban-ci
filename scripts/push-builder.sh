#!/usr/bin/env bash
set -e

if [ ! -f secrets/quay.env ]; then
    echo "secrets/quay.env not found!"
    exit 1
fi
source secrets/quay.env

echo "Logging in to Quay.io..."
echo "$QUAY_PASSWORD" | docker login -u "$QUAY_USERNAME" --password-stdin quay.io

# Handle robot accounts (format: org+robot)
# If '+' is present, use the part before it as the namespace
if [[ "$QUAY_USERNAME" == *"+"* ]]; then
    QUAY_NAMESPACE="${QUAY_USERNAME%%+*}"
    echo "Detected Robot Account. Using namespace: $QUAY_NAMESPACE"
else
    QUAY_NAMESPACE="$QUAY_USERNAME"
fi

BUILDER_TAG="quay.io/$QUAY_NAMESPACE/luban-builder:latest"
echo "Tagging builder as $BUILDER_TAG"
docker tag luban-ci/builder:latest "$BUILDER_TAG"

echo "Pushing builder..."
docker push "$BUILDER_TAG"
echo "Builder pushed successfully."
