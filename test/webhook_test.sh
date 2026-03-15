#!/bin/bash
set -e

# Default values if env vars are not set
GATEWAY_URL=${GATEWAY_URL:-"https://webhook-luban.metasync.cc/push"}
REPO_URL=${REPO_URL:-"https://github.com/metasync/luban-hello-world-py.git"}
REVISION=${REVISION:-""}
TAG=${TAG:-""}
APP_NAME=${APP_NAME:-"luban-hello-world-py"}
PROJECT_NAME=${PROJECT_NAME:-"metasync"}
K8S_NAMESPACE=${K8S_NAMESPACE:-"luban-ci"}
BRANCH=${BRANCH:-"main"}

echo "------------------------------------------------"
echo "Webhook Test Configuration:"
echo "GATEWAY_URL: $GATEWAY_URL"
echo "REPO_URL:    $REPO_URL"
echo "REVISION:    $REVISION"
echo "TAG:         $TAG"
echo "APP_NAME:    $APP_NAME"
echo "PROJECT_NAME:$PROJECT_NAME"
echo "------------------------------------------------"

# 1. Get Secret
echo "Retrieving webhook secret from Kubernetes..."
SECRET_B64=$(kubectl get secret webhook-secret -n "$K8S_NAMESPACE" -o jsonpath='{.data.secret}')
if [ -z "$SECRET_B64" ]; then
    echo "Error: Secret 'webhook-secret' not found in namespace '$K8S_NAMESPACE'"
    exit 1
fi

# Decode secret based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    SECRET=$(echo "$SECRET_B64" | base64 -D)
else
    SECRET=$(echo "$SECRET_B64" | base64 -d)
fi

# 2. Construct Payload
if [ -n "$TAG" ]; then
    REF="refs/tags/$TAG"
else
    REF="refs/heads/$BRANCH"
fi

if [ -z "$REVISION" ]; then
    REVISION=$(git ls-remote "$REPO_URL" HEAD 2>/dev/null | awk '{print $1}' | head -n 1)
fi

if [ -z "$REVISION" ]; then
    echo "Error: REVISION is empty (expected a git commit SHA)." >&2
    exit 1
fi

# Construct JSON payload using jq if available, otherwise raw string manipulation
# Using printf to safely format the JSON string
PAYLOAD=$(printf '{"ref":"%s","after":"%s","repository":{"clone_url":"%s","name":"%s"}}' \
    "$REF" "$REVISION" "$REPO_URL" "$APP_NAME")

# 3. Calculate Signature (HMAC-SHA256)
# OpenSSL is standard on most systems
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')
if [ -z "$SIGNATURE" ]; then
    # Fallback for older openssl versions or different output formats
    SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')
fi

# 4. Send Request
echo "Sending webhook request..."
curl -v -k -X POST "$GATEWAY_URL" \
    -H "Content-Type: application/json" \
    -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
    -H "X-GitHub-Event: push" \
    -H "User-Agent: GitHub-Hookshot/test-shell" \
    -d "$PAYLOAD"

echo ""
echo "------------------------------------------------"
echo "Request sent. Checking for triggered workflows..."
sleep 2
kubectl get wf -n "$K8S_NAMESPACE" --sort-by=.metadata.creationTimestamp
