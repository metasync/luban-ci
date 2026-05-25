#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"

PROJECT_NAME=${1:-}
VISIBILITY=${2:-}

[ -n "$PROJECT_NAME" ] || die "Error: project_name arg is required"
[ -n "$VISIBILITY" ] || die "Error: registry_visibility arg is required"

case "$VISIBILITY" in public|private) ;; *) die "Error: registry_visibility must be public|private: $VISIBILITY" ;; esac

require_env REGISTRY_SERVER
require_env HARBOR_USERNAME
require_env HARBOR_PASSWORD

require_no_cntrl project_name "$PROJECT_NAME"

HARBOR_URL="https://${REGISTRY_SERVER}"

PUBLIC=false
if [ "$VISIBILITY" = "public" ]; then
  PUBLIC=true
fi

if ! command -v jq >/dev/null 2>&1; then
  die "Error: missing 'jq' binary required to build request payload"
fi

PAYLOAD=$(
  jq -n \
    --arg project_name "$PROJECT_NAME" \
    --argjson public "$PUBLIC" \
    '{project_name: $project_name, public: $public, metadata: {public: ($public|tostring)}}'
)

echo "Creating project '${PROJECT_NAME}' on ${HARBOR_URL}..."

BODY_FILE=$(mktemp)
trap 'rm -f "$BODY_FILE"' EXIT

STATUS_CODE=$(
  curl -sS \
    -o "$BODY_FILE" \
    -w '%{http_code}' \
    -u "${HARBOR_USERNAME}:${HARBOR_PASSWORD}" \
    -X POST "${HARBOR_URL}/api/v2.0/projects" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD"
)

case "$STATUS_CODE" in
  201)
    echo "Project created successfully."
    ;;
  409)
    echo "Project already exists."
    ;;
  *)
    echo "Failed to create project. HTTP status: ${STATUS_CODE}" >&2
    cat "$BODY_FILE" >&2 || true
    exit 1
    ;;
esac

