#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"

ENVIRONMENT=${1:-}
PROJECT_NAME_RAW=${2:-}
GIT_PROVIDER=${3:-}
GIT_ORG_RAW=${4:-}
ADMIN_GROUP=${5:-}
DEVELOPER_GROUP=${6:-}

[ -n "$ENVIRONMENT" ] || die "Error: environment arg is required"
[ -n "$PROJECT_NAME_RAW" ] || die "Error: project_name arg is required"
[ -n "$GIT_PROVIDER" ] || die "Error: git_provider arg is required"

case "$ENVIRONMENT" in snd|prd) ;; *) die "Error: invalid environment: $ENVIRONMENT" ;; esac

require_env CLUSTER_MAP
require_no_cntrl project_name "$PROJECT_NAME_RAW"
require_dns_label project_name "$PROJECT_NAME_RAW"

PROJECT_NAME="${ENVIRONMENT}-${PROJECT_NAME_RAW}"

GIT_ORG=$GIT_ORG_RAW
if [ -z "$GIT_ORG" ]; then
  GIT_ORG=$PROJECT_NAME_RAW
fi

require_no_cntrl git_organization "$GIT_ORG"
if ! printf '%s' "$GIT_ORG" | grep -Eq '^[A-Za-z0-9._-]+$'; then
  die "Error: invalid git_organization: $GIT_ORG"
fi

require_no_cntrl admin_group "$ADMIN_GROUP"
require_no_cntrl developer_group "$DEVELOPER_GROUP"
require_group_name admin_group "$ADMIN_GROUP"
require_group_name developer_group "$DEVELOPER_GROUP"

ADMIN_GROUPS_BLOCK=""
DEVELOPER_GROUPS_BLOCK=""
if [ -n "$ADMIN_GROUP" ]; then
  ADMIN_GROUPS_BLOCK="groups: [\"${ADMIN_GROUP}\"]"
fi
if [ -n "$DEVELOPER_GROUP" ]; then
  DEVELOPER_GROUPS_BLOCK="groups: [\"${DEVELOPER_GROUP}\"]"
fi

GIT_SERVER=github.com
if [ "$GIT_PROVIDER" = "azure" ]; then
  GIT_SERVER=${AZURE_SERVER:-dev.azure.com}
elif [ "$GIT_PROVIDER" = "ado" ]; then
  if [ -z "${ADO_SERVER:-}" ]; then
    die "Error: missing ado_server in luban-config"
  fi
  GIT_SERVER=$ADO_SERVER
elif [ "$GIT_PROVIDER" = "github" ]; then
  GIT_SERVER=${GITHUB_SERVER:-github.com}
else
  die "Error: invalid git_provider: $GIT_PROVIDER"
fi

BASE_URL=${GIT_BASE_URL:-https://${GIT_SERVER}}
if { [ "$GIT_PROVIDER" = "azure" ] || [ "$GIT_PROVIDER" = "ado" ]; } && [ -n "$GIT_ORG_RAW" ]; then
  GITOPS_REPOS_WHITELIST="${BASE_URL}/${GIT_ORG}/${PROJECT_NAME_RAW}/_git/*"
else
  GITOPS_REPOS_WHITELIST="${BASE_URL}/${GIT_ORG}/*"
fi

DEST_SERVER=$(printf '%s' "$CLUSTER_MAP" | jq -r --arg env "$ENVIRONMENT" '.[$env]')
if [ -z "$DEST_SERVER" ] || [ "$DEST_SERVER" = "null" ]; then
  echo "Error: Could not find cluster URL for environment '$ENVIRONMENT' in cluster_map." >&2
  echo "Cluster Map: $CLUSTER_MAP" >&2
  exit 1
fi

echo "Creating AppProject ${PROJECT_NAME}..."

cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: ${PROJECT_NAME}
  namespace: argocd
spec:
  description: "${PROJECT_NAME_RAW} team project for ${ENVIRONMENT} environment"
  sourceRepos:
  - "${GITOPS_REPOS_WHITELIST}"
  destinations:
  - namespace: ${PROJECT_NAME}
    server: "${DEST_SERVER}"
  - namespace: gateway
    server: "${DEST_SERVER}"
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  namespaceResourceWhitelist:
  - group: '*'
    kind: '*'
  roles:
  - name: project-developer
    description: Developer role with read and sync access
    ${DEVELOPER_GROUPS_BLOCK}
    policies:
    - "p, proj:${PROJECT_NAME}:project-developer, applications, get, ${PROJECT_NAME}/*, allow"
    - "p, proj:${PROJECT_NAME}:project-developer, applications, sync, ${PROJECT_NAME}/*, allow"
  - name: project-admin
    description: Admin role with full access
    ${ADMIN_GROUPS_BLOCK}
    policies:
    - "p, proj:${PROJECT_NAME}:project-admin, applications, *, ${PROJECT_NAME}/*, allow"
EOF
