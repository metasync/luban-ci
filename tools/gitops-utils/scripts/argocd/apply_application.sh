#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"

ENVIRONMENT=${1:-}
PROJECT_NAME_RAW=${2:-}
APP_NAME_RAW=${3:-}
GIT_PROVIDER=${4:-}
GIT_ORG_RAW=${5:-}

[ -n "$ENVIRONMENT" ] || die "Error: environment arg is required"
[ -n "$PROJECT_NAME_RAW" ] || die "Error: project_name arg is required"
[ -n "$APP_NAME_RAW" ] || die "Error: app_name arg is required"
[ -n "$GIT_PROVIDER" ] || die "Error: git_provider arg is required"

case "$ENVIRONMENT" in snd|prd) ;; *) die "Error: invalid environment: $ENVIRONMENT" ;; esac

require_env GIT_SERVER
require_env CLUSTER_MAP

require_no_cntrl project_name "$PROJECT_NAME_RAW"
require_no_cntrl app_name "$APP_NAME_RAW"
require_dns_label project_name "$PROJECT_NAME_RAW"
require_dns_label app_name "$APP_NAME_RAW"

GIT_ORG=$GIT_ORG_RAW
if [ -z "$GIT_ORG" ]; then
  GIT_ORG=$PROJECT_NAME_RAW
fi

require_no_cntrl git_organization "$GIT_ORG"
if ! printf '%s' "$GIT_ORG" | grep -Eq '^[A-Za-z0-9._-]+$'; then
  die "Error: invalid git_organization: $GIT_ORG"
fi

REVISION=main
if [ "$ENVIRONMENT" = "snd" ]; then
  REVISION=develop
fi

BASE_URL=${GIT_BASE_URL:-https://${GIT_SERVER}}

if { [ "$GIT_PROVIDER" = "azure" ] || [ "$GIT_PROVIDER" = "ado" ]; } && [ -n "$GIT_ORG_RAW" ]; then
  REPO_URL="${BASE_URL}/${GIT_ORG}/${PROJECT_NAME_RAW}/_git/${APP_NAME_RAW}-gitops"
else
  REPO_URL="${BASE_URL}/${GIT_ORG}/${APP_NAME_RAW}-gitops.git"
fi

SYNC_POLICY_BLOCK=""
if [ "$ENVIRONMENT" != "prd" ]; then
  SYNC_POLICY_BLOCK="automated:
      prune: true
      selfHeal: true"
fi

DEST_SERVER=$(printf '%s' "$CLUSTER_MAP" | jq -r --arg env "$ENVIRONMENT" '.[$env]')
if [ -z "$DEST_SERVER" ] || [ "$DEST_SERVER" = "null" ]; then
  echo "Error: Could not find cluster URL for environment '$ENVIRONMENT' in cluster_map." >&2
  echo "Cluster Map: $CLUSTER_MAP" >&2
  exit 1
fi

echo "Creating Application ${ENVIRONMENT}-${PROJECT_NAME_RAW}-${APP_NAME_RAW} in namespace argocd..."
echo "Target Cluster: $DEST_SERVER"

cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${ENVIRONMENT}-${PROJECT_NAME_RAW}-${APP_NAME_RAW}
  namespace: argocd
spec:
  project: ${ENVIRONMENT}-${PROJECT_NAME_RAW}
  source:
    repoURL: "${REPO_URL}"
    targetRevision: "${REVISION}"
    path: app/overlays/${ENVIRONMENT}
  destination:
    server: "${DEST_SERVER}"
    namespace: ${ENVIRONMENT}-${PROJECT_NAME_RAW}
  ignoreDifferences:
    - group: ""
      kind: Secret
      name: ${APP_NAME_RAW}-secret
      namespace: ${ENVIRONMENT}-${PROJECT_NAME_RAW}
      jsonPointers:
        - /data
        - /stringData
  syncPolicy:
    ${SYNC_POLICY_BLOCK}
    syncOptions:
      - CreateNamespace=true
EOF
