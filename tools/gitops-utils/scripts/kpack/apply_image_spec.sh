#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"
. "${SCRIPT_DIR}/../lib/kube.sh"

normalize_repo_url() {
  if [ "${GIT_PROVIDER:-}" = "azure" ]; then
    case "$REPO_URL" in
      git@*|ssh://*) ;;
      *)
        if printf '%s' "$REPO_URL" | grep -q 'dev.azure.com'; then
          echo "Detected Azure DevOps Services URL. Converting to SSH format..."
          path_part=$(printf '%s' "$REPO_URL" | sed -E 's|^https?://([^@/]+@)?dev\.azure\.com/||; s|/_git/|/|')
          REPO_URL="git@ssh.dev.azure.com:v3/${path_part}"
          echo "Converted URL: $REPO_URL"
        elif printf '%s' "$REPO_URL" | grep -Eq '^https?://([^@/]+@)?[^/]+\.visualstudio\.com/'; then
          echo "Detected legacy Azure DevOps Services URL. Converting to SSH format..."
          org=$(printf '%s' "$REPO_URL" | sed -E 's|^https?://([^@/]+@)?([^./]+)\.visualstudio\.com/.*$|\2|')
          path_part=$(printf '%s' "$REPO_URL" | sed -E 's|^https?://([^@/]+@)?[^/]+\.visualstudio\.com/||; s|/_git/|/|')
          REPO_URL="git@ssh.dev.azure.com:v3/${org}/${path_part}"
          echo "Converted URL: $REPO_URL"
        fi
        ;;
    esac
  fi

  if [ "${GIT_PROVIDER:-}" = "ado" ]; then
    case "$REPO_URL" in
      git@*|ssh://*) ;;
      *)
        if printf '%s' "$REPO_URL" | grep -q '/_git/'; then
          echo "Detected Azure DevOps Server URL. Converting to SSH format..."
          host=$(printf '%s' "$REPO_URL" | sed -E 's|^https?://([^@/]+@)?([^/:]+)(:[0-9]+)?/.*$|\2|')
          path_part=$(printf '%s' "$REPO_URL" | sed -E 's|^https?://([^@/]+@)?[^/]+||')
          if [ -n "$host" ] && [ -n "$path_part" ]; then
            REPO_URL="git@${host}:${path_part}"
            echo "Converted URL: $REPO_URL"
          fi
        fi
        ;;
    esac
  fi
}

validate_azure_ssh_secret() {
  if [ "${GIT_PROVIDER:-}" = "azure" ] || [ "${GIT_PROVIDER:-}" = "ado" ]; then
    case "$REPO_URL" in
      git@*:*|ssh://git@*) is_azure_ssh=1 ;;
      *) is_azure_ssh=0 ;;
    esac
  else
    is_azure_ssh=0
  fi

  if [ "$is_azure_ssh" -ne 1 ]; then
    return
  fi

  expected_git_host=""
  case "$REPO_URL" in
    ssh://git@*) expected_git_host=$(printf '%s' "$REPO_URL" | sed -E 's|^ssh://git@([^/:]+).*|\1|') ;;
    git@*:* ) expected_git_host=$(printf '%s' "$REPO_URL" | sed -E 's|^git@([^:]+):.*|\1|') ;;
  esac

  ssh_creds_secret="${GIT_PROVIDER}-ssh-creds"
  secret_git_host=$($KUBECTL -n "$TARGET_NAMESPACE" get secret "$ssh_creds_secret" -o jsonpath='{.metadata.annotations.kpack\.io/git}' 2>/dev/null || true)
  if [ -n "$expected_git_host" ] && [ -n "$secret_git_host" ] && [ "$expected_git_host" != "$secret_git_host" ]; then
    echo "Error: kpack git host mismatch for Azure SSH clone." >&2
    echo "- Repo URL host:      $expected_git_host" >&2
    echo "- ${ssh_creds_secret} kpack.io/git: $secret_git_host" >&2
    echo "Fix: set ${ssh_creds_secret} annotation kpack.io/git to '$expected_git_host' in namespace '$TARGET_NAMESPACE' (via CI infra repo), and ensure known_hosts includes that host key." >&2
    exit 1
  fi

  key_b64=""
  count=0
  while [ "$count" -lt 60 ]; do
    key_b64=$($KUBECTL -n "$TARGET_NAMESPACE" get secret "$ssh_creds_secret" -o jsonpath='{.data.ssh-privatekey}' 2>/dev/null || true)
    if [ -n "$key_b64" ] && [ "$key_b64" != "cGxhY2Vob2xkZXI=" ]; then
      break
    fi
    count=$((count + 1))
    sleep 2
  done

  if [ -z "$key_b64" ]; then
    die "Error: Secret ${ssh_creds_secret} is missing or does not contain ssh-privatekey."
  fi

  if [ "$key_b64" = "cGxhY2Vob2xkZXI=" ]; then
    die "Error: Secret ${ssh_creds_secret} still contains placeholder data after waiting."
  fi
}

secret_has_real_key() {
  secret_name=$1
  jsonpath_expr=$2

  if ! $KUBECTL -n "$TARGET_NAMESPACE" get secret "$secret_name" >/dev/null 2>&1; then
    return 1
  fi

  value=$($KUBECTL -n "$TARGET_NAMESPACE" get secret "$secret_name" -o "jsonpath=${jsonpath_expr}" 2>/dev/null || true)
  [ -n "$value" ] && [ "$value" != "cGxhY2Vob2xkZXI=" ]
}

compute_image_tag() {
  if [ "$MODE" = "tag" ]; then
    if ! printf '%s' "$GIT_REF" | grep -q '^refs/tags/'; then
      die "Error: mode=tag but git_ref is not a tag: $GIT_REF"
    fi
    image_tag=${GIT_REF#refs/tags/}
    IMAGE_TAG=${image_tag#v}
  else
    IMAGE_TAG=${TAG:-$REVISION}
  fi

  require_image_tag image_tag "$IMAGE_TAG"
}

write_image_spec() {
  base_image_name="${registry_server}/${REGISTRY_NAMESPACE}/${APP_NAME}"
  image_spec_file=/tmp/kpack-image.yaml

  cat >"$image_spec_file" <<EOF
apiVersion: kpack.io/v1alpha2
kind: Image
metadata:
  name: $APP_NAME
  namespace: $TARGET_NAMESPACE
spec:
  tag: ${base_image_name}:latest
  additionalTags:
EOF

  if [ "$MODE" = "tag" ]; then
    echo "  - \"${base_image_name}:${REVISION}\"" >>"$image_spec_file"
  fi
  echo "  - \"${base_image_name}:${IMAGE_TAG}\"" >>"$image_spec_file"

  cat >>"$image_spec_file" <<EOF
  builder:
    kind: ClusterBuilder
    name: luban-builder
  source:
    git:
      url: "$REPO_URL"
      revision: "$REVISION"
    subPath: "$SUB_PATH"
  serviceAccountName: workflow-runner
  build:
EOF

  if [ "$HAS_UV_NETRC" -eq 1 ] || [ "$HAS_LUBAN_CA_CERT" -eq 1 ]; then
    echo "    services:" >>"$image_spec_file"
    if [ "$HAS_UV_NETRC" -eq 1 ]; then
      cat >>"$image_spec_file" <<EOF
      - name: uv-mirror-netrc
        kind: Secret
        apiVersion: v1
EOF
    fi
    if [ "$HAS_LUBAN_CA_CERT" -eq 1 ]; then
      cat >>"$image_spec_file" <<EOF
      - name: luban-ca-cert
        kind: Secret
        apiVersion: v1
EOF
    fi
  fi

  cat >>"$image_spec_file" <<EOF
    env:
      - name: BP_UV_RELEASE_BASE_URL
        valueFrom:
          configMapKeyRef:
            name: luban-config
            key: uv_release_base_url
            optional: true
      - name: BP_UV_PYTHON_INSTALL_MIRROR
        valueFrom:
          configMapKeyRef:
            name: luban-config
            key: uv_python_install_mirror
            optional: true
EOF

  if [ "$MODE" = "tag" ]; then
    cat >>"$image_spec_file" <<EOF
      - name: CI_TAG_UPDATE
        value: "${IMAGE_TAG}"
EOF
  fi

  kubectl apply -f "$image_spec_file"
}

MODE=${1:-}
SUB_PATH=${2:-}

[ -n "$MODE" ] || die "Error: mode argument is required"

require_env REGISTRY_NAMESPACE
require_env REVISION
require_env APP_NAME
require_env REPO_URL
require_env GIT_REF
require_env registry_server
require_env KUBERNETES_SERVICE_HOST
require_env KUBERNETES_SERVICE_PORT

mkdir -p /tmp
: >/tmp/image_tag

configure_incluster_kubeconfig

KUBECTL='kubectl --request-timeout=5s'
TARGET_NAMESPACE="ci-${REGISTRY_NAMESPACE}"

require_dns_label target_namespace "$TARGET_NAMESPACE"
require_hex_rev revision "$REVISION"

if printf '%s' "$APP_NAME" | grep -q '[^a-z0-9-]'; then
  die "Error: APP_NAME must contain only lowercase letters, digits, and '-': $APP_NAME"
fi

require_no_cntrl repo_url "$REPO_URL"
require_no_cntrl sub_path "$SUB_PATH"

if printf '%s' "$REPO_URL" | grep -q '"'; then
  die 'Error: repo_url contains an unsupported character: "'
fi

if printf '%s' "$SUB_PATH" | grep -q '"'; then
  die 'Error: sub_path contains an unsupported character: "'
fi

compute_image_tag
printf '%s' "$IMAGE_TAG" >/tmp/image_tag

normalize_repo_url
validate_azure_ssh_secret

HAS_UV_NETRC=0
if secret_has_real_key uv-mirror-netrc '{.data.netrc}'; then
  HAS_UV_NETRC=1
fi

HAS_LUBAN_CA_CERT=0
if secret_has_real_key luban-ca-cert '{.data.ca\.crt}'; then
  HAS_LUBAN_CA_CERT=1
fi

echo "Processing $MODE build for ${APP_NAME}..."
echo "Source Revision:  $REVISION"
echo "Target Image Tag: $IMAGE_TAG"

write_image_spec

echo "Image resource updated."
