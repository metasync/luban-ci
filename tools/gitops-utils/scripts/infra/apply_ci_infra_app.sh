#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"
. "${SCRIPT_DIR}/../lib/kube.sh"

PROJECT_NAME=${1:-}
GIT_ORG_RAW=${2:-}
GIT_PROVIDER=${3:-}

[ -n "$PROJECT_NAME" ] || die "Error: project_name arg is required"
[ -n "$GIT_PROVIDER" ] || die "Error: git_provider arg is required"

require_env GIT_SERVER

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

REPO_NAME="luban-infra-ci"
INFRA_PROJECT="luban-infra"

BASE_URL=${GIT_BASE_URL:-https://${GIT_SERVER}}
if [ "$GIT_PROVIDER" = "azure" ] || [ "$GIT_PROVIDER" = "ado" ]; then
  REPO_URL="${BASE_URL}/${GIT_ORG}/${INFRA_PROJECT}/_git/${REPO_NAME}"
else
  REPO_URL="${BASE_URL}/${GIT_ORG}/${REPO_NAME}.git"
fi

APP_NAME="ci-${PROJECT_NAME}-infra"
DEST_SERVER="https://kubernetes.default.svc"
NAMESPACE="ci-${PROJECT_NAME}"

echo "Creating CI Infra App $APP_NAME..."

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
    path: overlays/ci-${PROJECT_NAME}
  destination:
    server: "${DEST_SERVER}"
    namespace: "${NAMESPACE}"
  ignoreDifferences:
    - group: ""
      kind: Secret
      name: azure-ssh-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: ado-ssh-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: github-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: azure-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: ado-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: quay-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: harbor-creds
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: uv-mirror-netrc
      namespace: ${NAMESPACE}
      jsonPointers: ["/data", "/stringData"]
    - group: ""
      kind: Secret
      name: project-admin.service-account-token
      namespace: ${NAMESPACE}
      jsonPointers:
        - /data
        - /metadata/annotations/kubernetes.io~1service-account.uid
        - /metadata/ownerReferences
    - group: ""
      kind: Secret
      name: project-developer.service-account-token
      namespace: ${NAMESPACE}
      jsonPointers:
        - /data
        - /metadata/annotations/kubernetes.io~1service-account.uid
        - /metadata/ownerReferences
    - group: ""
      kind: ConfigMap
      name: luban-config
      namespace: ${NAMESPACE}
      jsonPointers: ["/data"]
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
EOF
