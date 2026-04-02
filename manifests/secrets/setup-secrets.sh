#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

load_env_files() {
  local env_dir="$1"

  if [ ! -d "$env_dir" ]; then
    return 0
  fi

  local f
  for f in "$env_dir"/*.env; do
    [ -f "$f" ] || continue

    local line trimmed key val
    while IFS= read -r line || [ -n "$line" ]; do
      line=${line%$'\r'}

      trimmed=${line#"${line%%[!$'\t ']*}"}
      if [ -z "$trimmed" ] || [ "${trimmed#\#}" != "$trimmed" ]; then
        continue
      fi

      if [[ "$trimmed" == export[[:space:]]* ]]; then
        trimmed=${trimmed#export}
        trimmed=${trimmed#"${trimmed%%[!$'\t ']*}"}
      fi

      if [[ "$trimmed" != *"="* ]]; then
        continue
      fi

      key=${trimmed%%=*}
      val=${trimmed#*=}

      key=${key%"${key##*[!$'\t ']}"}
      key=${key#"${key%%[!$'\t ']*}"}

      if ! [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
        echo "Error: invalid env key in $f: $key" >&2
        exit 1
      fi

      if [ "${val:0:1}" = "\"" ] && [ "${val: -1}" = "\"" ] && [ ${#val} -ge 2 ]; then
        val=${val:1:${#val}-2}
      elif [ "${val:0:1}" = "'" ] && [ "${val: -1}" = "'" ] && [ ${#val} -ge 2 ]; then
        val=${val:1:${#val}-2}
      fi

      val=${val//\$\$/\$}

      if [ -z "${!key:-}" ]; then
        export "$key=$val"
      fi
    done < "$f"
  done
}

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

load_env_files "${ROOT_DIR}/secrets"
K8S_NAMESPACE=${K8S_NAMESPACE:-luban-ci}
ARGOCD_NAMESPACE=${ARGOCD_NAMESPACE:-argocd}
CERT_MANAGER_NAMESPACE=${CERT_MANAGER_NAMESPACE:-cert-manager}

export K8S_NAMESPACE ARGOCD_NAMESPACE CERT_MANAGER_NAMESPACE

require() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Error: missing required env var: $name" >&2
    exit 1
  fi
}

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl is required" >&2
  exit 1
fi

KUBECTL="kubectl --request-timeout=10s"

TEMPLATES_DIR="${ROOT_DIR}/manifests/secrets/templates"

if ! command -v perl >/dev/null 2>&1; then
  echo "Error: perl is required for rendering manifests/secrets/templates" >&2
  exit 1
fi

render() {
  perl -pe 's/\$\{([A-Za-z_][A-Za-z0-9_]*)\}/exists $ENV{$1} ? $ENV{$1} : $&/ge'
}

apply_template() {
  local template_file="$1"
  local rendered
  rendered=$(mktemp)
  render < "${TEMPLATES_DIR}/${template_file}" > "$rendered"

  if grep -Eq '\$\{[A-Za-z_][A-Za-z0-9_]*\}' "$rendered"; then
    echo "Error: unresolved template variables in ${template_file}" >&2
    rm -f "$rendered"
    exit 1
  fi

  apply_yaml < "$rendered"
  rm -f "$rendered"
}

create_dockerconfigjson_secret() {
  local secret_name="$1"
  local namespace="$2"
  local server="$3"
  local username="$4"
  local password="$5"
  local email="$6"
  local allowed_namespaces="$7"
  local AUTH_B64
  local DOCKERCONFIGJSON

  export SECRET_NAME="$secret_name"
  export NAMESPACE="$namespace"
  export REPLICATION_ALLOWED_NAMESPACES="$allowed_namespaces"
  export DOCKERCONFIGJSON_B64

  AUTH_B64=$(printf '%s' "${username}:${password}" | base64 | tr -d '\n')
  DOCKERCONFIGJSON=$(printf '{"auths":{"%s":{"username":"%s","password":"%s","email":"%s","auth":"%s"}}}' \
    "$server" "$username" "$password" "$email" "$AUTH_B64")
  DOCKERCONFIGJSON_B64=$(printf '%s' "$DOCKERCONFIGJSON" | base64 | tr -d '\n')

  apply_template dockerconfigjson-secret.yaml.tmpl
  strip_last_applied secret "$SECRET_NAME" "$NAMESPACE"
}

create_ssh_auth_secret() {
  local secret_name="$1"
  local namespace="$2"
  local privatekey_path="$3"
  local known_hosts_path="$4"
  local kpack_git_annotation="$5"

  if [ ! -f "$privatekey_path" ]; then
    echo "Error: missing SSH private key: $privatekey_path" >&2
    exit 1
  fi
  if [ ! -f "$known_hosts_path" ]; then
    echo "Error: missing known_hosts: $known_hosts_path" >&2
    exit 1
  fi

  export SECRET_NAME="$secret_name"
  export NAMESPACE="$namespace"
  export KPACK_GIT_ANNOTATION="$kpack_git_annotation"
  export SSH_PRIVATEKEY_B64
  export KNOWN_HOSTS_B64
  SSH_PRIVATEKEY_B64=$($KUBECTL create secret generic "$SECRET_NAME" \
    -n "$NAMESPACE" \
    --type=kubernetes.io/ssh-auth \
    --from-file=ssh-privatekey="$privatekey_path" \
    --dry-run=client \
    -o go-template='{{ index .data "ssh-privatekey" }}')
  KNOWN_HOSTS_B64=$($KUBECTL create secret generic "$SECRET_NAME" \
    -n "$NAMESPACE" \
    --type=kubernetes.io/ssh-auth \
    --from-file=known_hosts="$known_hosts_path" \
    --dry-run=client \
    -o go-template='{{ index .data "known_hosts" }}')

  apply_template ssh-auth-secret.yaml.tmpl
}

create_netrc_binding_secret() {
  local secret_name="$1"
  local namespace="$2"
  local allowed_namespaces="$3"
  local netrc_text="$4"

  export SECRET_NAME="$secret_name"
  export NAMESPACE="$namespace"
  export REPLICATION_ALLOWED_NAMESPACES="$allowed_namespaces"
  export BINDING_TYPE_B64
  export BINDING_PROVIDER_B64
  export NETRC_B64

  BINDING_TYPE_B64=$(printf '%s' 'netrc' | base64 | tr -d '\n')
  BINDING_PROVIDER_B64=$(printf '%s' 'luban-ci' | base64 | tr -d '\n')
  NETRC_B64=$(printf '%s' "$netrc_text" | base64 | tr -d '\n')

  apply_template netrc-service-binding-secret.yaml.tmpl
  strip_last_applied secret "$SECRET_NAME" "$NAMESPACE"
}

create_argocd_repo_creds_secret() {
  local secret_name="$1"
  local namespace="$2"
  local repo_url="$3"
  local username="$4"
  local password="$5"

  export SECRET_NAME="$secret_name"
  export NAMESPACE="$namespace"
  export REPO_URL="$repo_url"
  export USERNAME="$username"
  export PASSWORD="$password"

  apply_template argocd-repo-creds.yaml.tmpl
}

require REGISTRY_EMAIL
require QUAY_USERNAME
require QUAY_PASSWORD
require HARBOR_SERVER
require HARBOR_USERNAME
require HARBOR_PASSWORD
require HARBOR_RO_USERNAME
require HARBOR_RO_PASSWORD

REGISTRY_SERVER=${REGISTRY_SERVER:-quay.io}

apply_yaml() {
  if [ "$DRY_RUN" = "1" ]; then
    $KUBECTL apply --server-side --dry-run=server -f - >/dev/null
  else
    $KUBECTL apply --server-side -f - >/dev/null
  fi
}

strip_last_applied() {
  local kind="$1"
  local name="$2"
  local namespace="$3"

  if [ "$DRY_RUN" = "1" ]; then
    return 0
  fi

  local existing
  existing=$($KUBECTL get "$kind" "$name" -n "$namespace" -o jsonpath='{.metadata.annotations.kubectl\.kubernetes\.io/last-applied-configuration}' 2>/dev/null || true)
  if [ -n "$existing" ]; then
    $KUBECTL annotate "$kind" "$name" -n "$namespace" kubectl.kubernetes.io/last-applied-configuration- >/dev/null
  fi
}

$KUBECTL create ns "$K8S_NAMESPACE" --dry-run=client -o yaml | $KUBECTL apply -f -
$KUBECTL create ns "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | $KUBECTL apply -f -


if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
  $KUBECTL create ns "$CERT_MANAGER_NAMESPACE" --dry-run=client -o yaml | $KUBECTL apply -f -
fi

create_dockerconfigjson_secret quay-creds "$K8S_NAMESPACE" "$REGISTRY_SERVER" "$QUAY_USERNAME" "$QUAY_PASSWORD" "$REGISTRY_EMAIL" "^ci-.*"
create_dockerconfigjson_secret harbor-creds "$K8S_NAMESPACE" "$HARBOR_SERVER" "$HARBOR_USERNAME" "$HARBOR_PASSWORD" "$REGISTRY_EMAIL" "^ci-.*"
create_dockerconfigjson_secret harbor-ro-creds "$K8S_NAMESPACE" "$HARBOR_SERVER" "$HARBOR_RO_USERNAME" "$HARBOR_RO_PASSWORD" "$REGISTRY_EMAIL" "^(snd|prd)-.*"

apply_template harbor-api-creds.yaml.tmpl
strip_last_applied secret harbor-api-creds "$K8S_NAMESPACE"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  require GITHUB_USERNAME
  require GITHUB_ORGANIZATION
  apply_template github-creds.yaml.tmpl
  strip_last_applied secret github-creds "$K8S_NAMESPACE"
fi

if [ -n "${AZURE_DEVOPS_TOKEN:-}" ]; then
  require AZURE_ORGANIZATION
  apply_template azure-creds.yaml.tmpl
  strip_last_applied secret azure-creds "$K8S_NAMESPACE"
fi

if [ -n "${ADO_DEVOPS_TOKEN:-}" ]; then
  apply_template ado-creds.yaml.tmpl
  strip_last_applied secret ado-creds "$K8S_NAMESPACE"
fi

if [ -n "${AZURE_DEVOPS_TOKEN:-}" ]; then
  AZURE_SSH_HOST=${AZURE_SSH_HOST:-${AZURE_SERVER:-ssh.dev.azure.com}}
  AZURE_SSH_HOST=$(printf "%s" "$AZURE_SSH_HOST" | sed -E 's|^https?://||; s|/.*$||; s|:.*$||')
  create_ssh_auth_secret azure-ssh-creds "$K8S_NAMESPACE" "${ROOT_DIR}/secrets/azure_id_rsa" "${ROOT_DIR}/secrets/known_hosts" "$AZURE_SSH_HOST"
  strip_last_applied secret azure-ssh-creds "$K8S_NAMESPACE"
fi

if [ -n "${ADO_SSH_HOST:-${ADO_SERVER:-}}" ] && [ -f "${ROOT_DIR}/secrets/ado_id_rsa" ]; then
  ADO_SSH_HOST=${ADO_SSH_HOST:-${ADO_SERVER}}
  ADO_SSH_HOST=$(printf "%s" "$ADO_SSH_HOST" | sed -E 's|^https?://||; s|/.*$||; s|:.*$||')
  create_ssh_auth_secret ado-ssh-creds "$K8S_NAMESPACE" "${ROOT_DIR}/secrets/ado_id_rsa" "${ROOT_DIR}/secrets/known_hosts" "$ADO_SSH_HOST"
  strip_last_applied secret ado-ssh-creds "$K8S_NAMESPACE"
fi

normalize_host() {
  printf "%s" "$1" | sed -E 's|^https?://||; s|/.*$||; s|:.*$||'
}

append_netrc_entry() {
  local host="$1"
  local username="$2"
  local password="$3"
  NETRC_CONTENT="${NETRC_CONTENT}$(printf "machine %s\n  login %s\n  password %s\n" "$host" "$username" "$password")"
}

NETRC_CONTENT=""
UV_MIRROR_HOST_NORM=""

if [ -n "${UV_MIRROR_HOST:-}" ]; then
  if [ -z "${UV_MIRROR_USERNAME:-}" ] || [ -z "${UV_MIRROR_PASSWORD:-}" ]; then
    echo "Error: UV_MIRROR_HOST is set but UV_MIRROR_USERNAME/UV_MIRROR_PASSWORD are missing" >&2
    exit 1
  fi
  UV_MIRROR_HOST_NORM=$(normalize_host "$UV_MIRROR_HOST")
  append_netrc_entry "$UV_MIRROR_HOST_NORM" "$UV_MIRROR_USERNAME" "$UV_MIRROR_PASSWORD"
fi

if [ -n "${UV_PYTHON_MIRROR_HOST:-}" ]; then
  UV_PYTHON_MIRROR_HOST_NORM=$(normalize_host "$UV_PYTHON_MIRROR_HOST")
  if [ "$UV_PYTHON_MIRROR_HOST_NORM" != "$UV_MIRROR_HOST_NORM" ]; then
    if [ -n "${UV_PYTHON_MIRROR_USERNAME:-}" ] && [ -n "${UV_PYTHON_MIRROR_PASSWORD:-}" ]; then
      append_netrc_entry "$UV_PYTHON_MIRROR_HOST_NORM" "$UV_PYTHON_MIRROR_USERNAME" "$UV_PYTHON_MIRROR_PASSWORD"
    elif [ -n "${UV_MIRROR_USERNAME:-}" ] && [ -n "${UV_MIRROR_PASSWORD:-}" ]; then
      append_netrc_entry "$UV_PYTHON_MIRROR_HOST_NORM" "$UV_MIRROR_USERNAME" "$UV_MIRROR_PASSWORD"
    else
      echo "Error: UV_PYTHON_MIRROR_HOST is set but no credentials provided (set UV_PYTHON_MIRROR_USERNAME/UV_PYTHON_MIRROR_PASSWORD or UV_MIRROR_USERNAME/UV_MIRROR_PASSWORD)" >&2
      exit 1
    fi
  fi
fi

if [ -n "$NETRC_CONTENT" ]; then
  create_netrc_binding_secret uv-mirror-netrc "$K8S_NAMESPACE" "^ci-.*" "$NETRC_CONTENT"
fi

if [ -n "${CLOUDFLARE_API_TOKEN:-}" ]; then
  apply_template cloudflare-api-token.yaml.tmpl
  strip_last_applied secret cloudflare-api-token "$CERT_MANAGER_NAMESPACE"
fi

if [ -n "${AZURE_DEVOPS_TOKEN:-}" ]; then
  require AZURE_ORGANIZATION
  create_argocd_repo_creds_secret argocd-repo-creds-azure "$ARGOCD_NAMESPACE" "https://dev.azure.com/${AZURE_ORGANIZATION}" "git" "${AZURE_DEVOPS_TOKEN}"
  strip_last_applied secret argocd-repo-creds-azure "$ARGOCD_NAMESPACE"
fi

if [ -n "${ADO_DEVOPS_TOKEN:-}" ] && [ -n "${ADO_COLLECTION:-}" ]; then
  ADO_BASE_URL=${ADO_BASE_URL:-}
  if [ -z "$ADO_BASE_URL" ] && [ -n "${ADO_SERVER:-}" ]; then
    ADO_BASE_URL="https://${ADO_SERVER}"
  fi
  ADO_BASE_URL=$(printf "%s" "$ADO_BASE_URL" | sed -E 's|/*$||')
  if [ -n "$ADO_BASE_URL" ]; then
    create_argocd_repo_creds_secret argocd-repo-creds-ado "$ARGOCD_NAMESPACE" "${ADO_BASE_URL}/${ADO_COLLECTION}" "git" "${ADO_DEVOPS_TOKEN}"
    strip_last_applied secret argocd-repo-creds-ado "$ARGOCD_NAMESPACE"
  fi
fi
if [ -n "${GITHUB_TOKEN:-}" ]; then
  require GITHUB_ORGANIZATION
  create_argocd_repo_creds_secret argocd-repo-creds-github "$ARGOCD_NAMESPACE" "https://github.com/${GITHUB_ORGANIZATION}" "luban-ci" "${GITHUB_TOKEN}"
  strip_last_applied secret argocd-repo-creds-github "$ARGOCD_NAMESPACE"
fi

echo "Secrets setup complete."
