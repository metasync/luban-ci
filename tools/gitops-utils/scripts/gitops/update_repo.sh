#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"

compute_image_tag() {
  if printf '%s' "$GIT_REF" | grep -q '^refs/tags/'; then
    image_tag=${GIT_REF#refs/tags/}
    IMAGE_TAG=${image_tag#v}
  else
    IMAGE_TAG=${TAG:-$REVISION}
  fi
}

derive_gitops_repo_url() {
  if [ "$GIT_PROVIDER" = "azure" ] || [ "$GIT_PROVIDER" = "ado" ]; then
    if printf '%s' "$REPO_URL" | grep -q 'ssh.dev.azure.com'; then
      base_path=$(printf '%s' "$REPO_URL" | sed -E 's|.*v3/||')
      org_proj=$(printf '%s' "$base_path" | cut -d/ -f1,2)
      GITOPS_REPO_URL="https://dev.azure.com/${org_proj}/_git/${APP_NAME}-gitops"
    else
      if ! printf '%s' "$REPO_URL" | grep -q '/_git/'; then
        die "Error: Azure REPO_URL is missing '/_git/': $REPO_URL"
      fi
      GITOPS_REPO_URL="${REPO_URL%/_git/*}/_git/${APP_NAME}-gitops"
      if [ -z "$GITOPS_REPO_URL" ]; then
        die "Error: failed to derive GitOps repo URL from Azure REPO_URL: $REPO_URL"
      fi
    fi
    echo "Detected Azure DevOps. Constructed GitOps URL: $GITOPS_REPO_URL"
  else
    GITOPS_REPO_URL="https://${GIT_PROVIDER}.com/${REGISTRY_NAMESPACE}/${APP_NAME}-gitops.git"
  fi
}

run_git() {
  if [ "$AUTH_MODE" = "extraheader_basic" ]; then
    git -c http.extraHeader="$LUBAN_GIT_AUTH_HEADER" "$@"
  else
    git "$@"
  fi
}

configure_git_auth() {
  domain=$(printf '%s' "$GITOPS_REPO_URL" | sed -e 's|^[^/]*//||' -e 's|/.*$||')

  case "$AUTH_MODE" in
    credential_store)
      git config --global credential.helper store
      echo "https://${BASIC_USER}:${GIT_TOKEN}@${domain}" >"${HOME}/.git-credentials"
      ;;
    extraheader_basic)
      if ! command -v base64 >/dev/null 2>&1; then
        die "Error: missing 'base64' binary required for extraheader_basic auth"
      fi
      auth_b64=$(printf '%s' "${BASIC_USER}:${GIT_TOKEN}" | base64 | tr -d '\n')
      LUBAN_GIT_AUTH_HEADER="Authorization: Basic ${auth_b64}"
      export LUBAN_GIT_AUTH_HEADER
      ;;
    *)
      die "Error: invalid GIT_HTTPS_AUTH_MODE: ${AUTH_MODE}"
      ;;
  esac
}

checkout_branch() {
  if run_git show-ref --verify --quiet "refs/heads/${GITOPS_BRANCH}"; then
    run_git checkout "${GITOPS_BRANCH}"
    return
  fi

  if run_git ls-remote --exit-code --heads origin "${GITOPS_BRANCH}" >/dev/null 2>&1; then
    run_git checkout -b "${GITOPS_BRANCH}" "origin/${GITOPS_BRANCH}"
    return
  fi

  run_git checkout -b "${GITOPS_BRANCH}"
  run_git push -u origin "${GITOPS_BRANCH}"
}

update_kustomization() {
  if [ ! -f "$KUST_PATH" ]; then
    die "Error: missing kustomization file: ${KUST_PATH}"
  fi

  if yq -e '.images[] | select(.name == env(APP_IMAGE_NAME))' "$KUST_PATH" >/dev/null 2>&1; then
    yq -i 'with(.images[]; select(.name == env(APP_IMAGE_NAME)) | .newTag = env(IMAGE_TAG) | del(.newName))' "$KUST_PATH"
    return
  fi

  die "Error: Image entry for $APP_IMAGE_NAME not found in $KUST_PATH. Please ensure the GitOps repository is correctly provisioned with an images block for this application."
}

require_env DEPLOY_ENV
require_env GITOPS_BRANCH
require_env GIT_PROVIDER
require_env REPO_URL
require_env REGISTRY_NAMESPACE
require_env APP_NAME
require_env REVISION
require_env GIT_TOKEN
require_env GIT_USERNAME
require_env registry_server

case "$DEPLOY_ENV" in
  snd|prd) ;;
  *) die "Error: DEPLOY_ENV must be 'snd' or 'prd': ${DEPLOY_ENV}" ;;
esac

case "$GITOPS_BRANCH" in
  ""|*" "*|*".."*|*"~"*|*"^"*|*":"*|*"\\"*|*"?"*|*"*"*|*"["*|*"{"*|*"}"*)
    die "Error: invalid GITOPS_BRANCH: ${GITOPS_BRANCH}"
    ;;
esac

if ! printf '%s' "$GITOPS_BRANCH" | grep -Eq '^[A-Za-z0-9._/-]+$'; then
  die "Error: invalid GITOPS_BRANCH: ${GITOPS_BRANCH}"
fi

compute_image_tag
derive_gitops_repo_url

AUTH_MODE=${GIT_HTTPS_AUTH_MODE:-credential_store}
BASIC_USER=${GIT_BASIC_AUTH_USERNAME:-$GIT_USERNAME}
configure_git_auth

git config --global user.email "ci@luban.com"
git config --global user.name "Luban CI"

mkdir -p /workdir
echo "Cloning ${GITOPS_REPO_URL}..."
run_git clone "$GITOPS_REPO_URL" /workdir/gitops
cd /workdir/gitops

git config --global --add safe.directory /workdir/gitops
checkout_branch

KUST_PATH="app/overlays/${DEPLOY_ENV}/kustomization.yaml"
APP_IMAGE_NAME="${registry_server}/${REGISTRY_NAMESPACE}/${APP_NAME}"
export APP_IMAGE_NAME IMAGE_TAG

echo "Updating GitOps repo..."
echo "Updating image tag to $IMAGE_TAG..."

update_kustomization

if run_git diff --quiet; then
  echo "No changes to commit."
  exit 0
fi

run_git add .
run_git commit -m "Update ${APP_NAME} ${DEPLOY_ENV} image tag to ${IMAGE_TAG}"
run_git push
