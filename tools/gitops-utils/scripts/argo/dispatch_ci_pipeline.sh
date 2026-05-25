#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"
. "${SCRIPT_DIR}/../lib/kube.sh"

slugify_dns_label() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//; s/-+/-/g'
}

derive_namespace_scope() {
  repo_url=$1
  git_provider=$2

  url_stripped=$(printf '%s' "$repo_url" | sed -e 's|^[^/]*//||')
  host=$(printf '%s' "$url_stripped" | cut -d'/' -f1)
  path_part=$(printf '%s' "$url_stripped" | cut -d'/' -f2-)

  seg1=$(printf '%s' "$path_part" | cut -d'/' -f1)
  seg2=$(printf '%s' "$path_part" | cut -d'/' -f2)
  seg3=$(printf '%s' "$path_part" | cut -d'/' -f3)
  seg4=$(printf '%s' "$path_part" | cut -d'/' -f4)

  if printf '%s' "$host" | grep -q "\.visualstudio\.com$"; then
    org=$(printf '%s' "$host" | cut -d'.' -f1)
    project=$seg1

    if printf '%s' "$seg1" | tr '[:upper:]' '[:lower:]' | grep -qx "defaultcollection"; then
      if [ "$seg2" = "_git" ] && [ -n "$seg3" ]; then
        project=$seg3
      elif [ -n "$seg2" ] && [ "$seg3" = "_git" ]; then
        project=$seg2
      fi
    elif [ -n "$seg2" ] && [ "$seg3" = "_git" ]; then
      project=$seg1
    elif [ -n "$seg3" ] && [ "$seg4" = "_git" ]; then
      project=$seg2
    fi

    namespace_scope=$project
  elif [ "$host" = "ssh.dev.azure.com" ]; then
    if [ "$seg1" = "v3" ]; then
      org=$seg2
      project=$seg3
      namespace_scope=$project
    else
      org=$seg1
      namespace_scope=$org
    fi
  elif { [ "$git_provider" = "azure" ] || [ "$git_provider" = "ado" ]; } && printf '%s' "$path_part" | grep -q '/_git/'; then
    project=$(printf '%s' "$path_part" | awk -F/ '{for(i=1;i<=NF;i++) if($i=="_git") {print $(i-1); exit}}')
    if [ -z "$project" ]; then
      die "Error: Failed to derive Azure project from repo_url"
    fi
    namespace_scope=$project
  else
    org=$seg1
    namespace_scope=$org
  fi

  slug=$(slugify_dns_label "$namespace_scope")
  if [ -z "$slug" ]; then
    die "Error: Failed to derive a valid namespace scope from repo_url"
  fi
  require_dns_label namespace_scope "$slug"

  printf '%s' "$slug"
}

REPO_URL=${1:-}
REVISION=${2:-}
APP_NAME=${3:-}
GIT_REF=${4:-}
GIT_PROVIDER=${5:-}
GIT_CREDS_SECRET=${6:-}

[ -n "$REPO_URL" ] || die "Error: repo_url arg is required"
[ -n "$REVISION" ] || die "Error: revision arg is required"
[ -n "$APP_NAME" ] || die "Error: app_name arg is required"
[ -n "$GIT_REF" ] || die "Error: git_ref arg is required"
[ -n "$GIT_PROVIDER" ] || die "Error: git_provider arg is required"
[ -n "$GIT_CREDS_SECRET" ] || die "Error: git_creds_secret arg is required"

case "$GIT_PROVIDER" in github|azure|ado) ;; *) die "Error: invalid git_provider: $GIT_PROVIDER" ;; esac

require_no_cntrl repo_url "$REPO_URL"
require_no_cntrl app_name "$APP_NAME"
require_no_cntrl git_ref "$GIT_REF"
require_no_cntrl git_creds_secret "$GIT_CREDS_SECRET"

if [ -n "${KUBERNETES_SERVICE_HOST:-}" ] && [ -n "${KUBERNETES_SERVICE_PORT:-}" ]; then
  configure_incluster_kubeconfig
fi

NAMESPACE_SCOPE=$(derive_namespace_scope "$REPO_URL" "$GIT_PROVIDER")
TARGET_NS="ci-${NAMESPACE_SCOPE}"
require_dns_label target_namespace "$TARGET_NS"

DEPLOY_ENV="snd"

if ! kubectl get namespace "$TARGET_NS" >/dev/null 2>&1; then
  die "Error: Target namespace '$TARGET_NS' not found. Provision the tenant CI namespace first."
fi

echo "Dispatching CI pipeline for ${APP_NAME} to ${TARGET_NS} (GitOps Env: ${DEPLOY_ENV})..."

REGISTRY_SERVER_VALUE=${REGISTRY_SERVER:-}

argo submit \
  --from clusterworkflowtemplate/luban-ci-kpack-template \
  -n "$TARGET_NS" \
  --serviceaccount workflow-runner \
  -p repo_url="$REPO_URL" \
  -p registry_namespace="$NAMESPACE_SCOPE" \
  -p revision="$REVISION" \
  -p app_name="$APP_NAME" \
  -p git_ref="$GIT_REF" \
  -p git_provider="$GIT_PROVIDER" \
  -p git_creds_secret="$GIT_CREDS_SECRET" \
  -p deploy_env="$DEPLOY_ENV" \
  -p registry_server="$REGISTRY_SERVER_VALUE" \
  --labels "app=$APP_NAME"

