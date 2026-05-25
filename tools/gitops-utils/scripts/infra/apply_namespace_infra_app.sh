#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"
. "${SCRIPT_DIR}/../lib/kube.sh"

ENVIRONMENT=${1:-}
PROJECT_NAME=${2:-}
GIT_ORG_RAW=${3:-}
GIT_PROVIDER=${4:-}

[ -n "$ENVIRONMENT" ] || die "Error: environment arg is required"
[ -n "$PROJECT_NAME" ] || die "Error: project_name arg is required"
[ -n "$GIT_PROVIDER" ] || die "Error: git_provider arg is required"

case "$ENVIRONMENT" in snd|prd) ;; *) die "Error: invalid environment: $ENVIRONMENT" ;; esac

require_env GIT_SERVER
require_env CLUSTER_MAP

case "$GIT_PROVIDER" in github|azure|ado) ;; *) die "Error: invalid git_provider: $GIT_PROVIDER" ;; esac

require_no_cntrl project_name "$PROJECT_NAME"
require_dns_label project_name "$PROJECT_NAME"

GIT_ORG=$GIT_ORG_RAW
if [ -z "$GIT_ORG" ]; then
  GIT_ORG=$PROJECT_NAME
fi

require_no_cntrl git_organization "$GIT_ORG"
if ! printf '%s' "$GIT_ORG" | grep -Eq '^[A-Za-z0-9._-]+$'; then
  die "Error: invalid git_organization: $GIT_ORG"
fi

if [ -n "${KUBERNETES_SERVICE_HOST:-}" ] && [ -n "${KUBERNETES_SERVICE_PORT:-}" ]; then
  configure_incluster_kubeconfig
fi

REPO_NAME="luban-infra-cd"
INFRA_PROJECT="luban-infra"

BASE_URL=${GIT_BASE_URL:-https://${GIT_SERVER}}
if [ "$GIT_PROVIDER" = "azure" ] || [ "$GIT_PROVIDER" = "ado" ]; then
  REPO_URL="${BASE_URL}/${GIT_ORG}/${INFRA_PROJECT}/_git/${REPO_NAME}"
else
  REPO_URL="${BASE_URL}/${GIT_ORG}/${REPO_NAME}.git"
fi

APP_NAME="${ENVIRONMENT}-${PROJECT_NAME}-infra"
DEST_SERVER=$(printf '%s' "$CLUSTER_MAP" | jq -r --arg env "$ENVIRONMENT" '.[$env]')
if [ -z "$DEST_SERVER" ] || [ "$DEST_SERVER" = "null" ]; then
  echo "Error: Could not find cluster URL for environment $ENVIRONMENT" >&2
  exit 1
fi

NAMESPACE="${ENVIRONMENT}-${PROJECT_NAME}"

SYNC_POLICY_BLOCK=""
if [ "$ENVIRONMENT" != "prd" ]; then
  SYNC_POLICY_BLOCK="automated:
      prune: true
      selfHeal: true"
fi

echo "Creating Namespace Infra App $APP_NAME..."

if [ -n "${CILIUM_EGRESS_GATEWAY_POLICY:-}" ]; then
  if ! kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
    kubectl create namespace "${NAMESPACE}"
  fi
  kubectl label namespace "${NAMESPACE}" "luban-ci.io/cilium-egress-gateway-policy=${CILIUM_EGRESS_GATEWAY_POLICY}" --overwrite
fi

cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${APP_NAME}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: "${REPO_URL}"
    targetRevision: main
    path: overlays/${ENVIRONMENT}-${PROJECT_NAME}
  destination:
    server: "${DEST_SERVER}"
    namespace: "${NAMESPACE}"
  ignoreDifferences:
    - group: ""
      kind: Secret
      name: harbor-ro-creds
      namespace: ${NAMESPACE}
      jsonPointers:
        - /data
        - /stringData
  syncPolicy:
    ${SYNC_POLICY_BLOCK}
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
EOF
