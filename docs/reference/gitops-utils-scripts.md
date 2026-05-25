## gitops-utils scripts

The `gitops-utils` image ships a set of stable entrypoint scripts under `/usr/local/bin/*.sh`. Workflows should call these stable names.

Inside the image, implementations live under:

- `/opt/luban/gitops-utils/scripts/`
  - `bin/` (stable entrypoints)
  - domain folders (`argo/`, `argocd/`, `gitops/`, `harbor/`, `infra/`, `kpack/`)
  - `lib/` (shared helpers sourced via POSIX `.`)

### Entrypoint contracts

#### kpack_apply_image_spec.sh

- Purpose: Generate `/tmp/kpack-image.yaml`, apply the kpack `Image`, and write the resolved tag to `/tmp/image_tag`.
- Args:
  - `mode` (`commit|tag`)
  - `sub_path` (may be empty)
- Required env:
  - `REGISTRY_NAMESPACE`
  - `REVISION`
  - `APP_NAME`
  - `REPO_URL`
  - `GIT_REF`
  - `registry_server`
  - `KUBERNETES_SERVICE_HOST`
  - `KUBERNETES_SERVICE_PORT`
- Optional env:
  - `TAG`
  - `GIT_PROVIDER`
- Outputs:
  - `/tmp/kpack-image.yaml`
  - `/tmp/image_tag`

#### kpack_wait_build.sh

- Purpose: Wait for the kpack Build for `REVISION` to exist and complete; streams logs via `kp build logs`.
- Args: none
- Required env:
  - `REGISTRY_NAMESPACE`
  - `APP_NAME`
  - `REVISION`
  - `KUBERNETES_SERVICE_HOST`
  - `KUBERNETES_SERVICE_PORT`
- Outputs: none

#### gitops_update_repo.sh

- Purpose: Clone the app GitOps repo, update the image tag in `app/overlays/<env>/kustomization.yaml`, commit, and push.
- Args: none
- Required env:
  - `DEPLOY_ENV` (`snd|prd`)
  - `GITOPS_BRANCH`
  - `GIT_PROVIDER`
  - `REPO_URL`
  - `REGISTRY_NAMESPACE`
  - `APP_NAME`
  - `REVISION`
  - `GIT_USERNAME`
  - `GIT_TOKEN`
  - `registry_server`
  - `GIT_REF`
- Optional env:
  - `TAG`
  - `GIT_HTTPS_AUTH_MODE` (`credential_store|extraheader_basic`)
  - `GIT_BASIC_AUTH_USERNAME`

#### argocd_apply_application.sh

- Purpose: Apply an Argo CD `Application` for `${ENVIRONMENT}-${PROJECT}-${APP}` pointing at the app’s `*-gitops` repo.
- Args:
  - `environment` (`snd|prd`)
  - `project_name` (DNS label)
  - `app_name` (DNS label)
  - `git_provider`
  - `git_organization` (may be empty)
- Required env:
  - `GIT_SERVER`
  - `CLUSTER_MAP`
- Optional env:
  - `GIT_BASE_URL`

#### argocd_apply_appproject.sh

- Purpose: Apply an Argo CD `AppProject` for `${ENVIRONMENT}-${PROJECT}`, with optional OIDC group bindings.
- Args:
  - `environment` (`snd|prd`)
  - `project_name` (DNS label)
  - `git_provider`
  - `git_organization` (may be empty)
  - `admin_group` (may be empty)
  - `developer_group` (may be empty)
- Required env:
  - `CLUSTER_MAP`
- Required env (provider-specific):
  - `ADO_SERVER` (required when `git_provider=ado`)
- Optional env:
  - `GIT_BASE_URL`
  - `GITHUB_SERVER`
  - `AZURE_SERVER`

#### argocd_apply_namespace_infra_app.sh

- Purpose: Create/label `${ENVIRONMENT}-${PROJECT}` (optional) and apply the namespace infra Argo CD `Application` pointing at `luban-infra-cd`.
- Args:
  - `environment` (`snd|prd`)
  - `project_name`
  - `git_organization` (may be empty; defaults to `project_name`)
  - `git_provider` (`github|azure|ado`)
- Required env:
  - `GIT_SERVER`
  - `CLUSTER_MAP`
- Optional env:
  - `GIT_BASE_URL`
  - `CILIUM_EGRESS_GATEWAY_POLICY`

#### argocd_apply_ci_infra_app.sh

- Purpose: Create/label `ci-${PROJECT}` (optional) and apply the CI infra Argo CD `Application` pointing at `luban-infra-ci`.
- Args:
  - `project_name`
  - `git_organization` (may be empty; defaults to `project_name`)
  - `git_provider` (`github|azure|ado`)
- Required env:
  - `GIT_SERVER`
- Optional env:
  - `GIT_BASE_URL`
  - `CILIUM_EGRESS_GATEWAY_POLICY`

#### argo_dispatch_ci_pipeline.sh

- Purpose: Derive tenant namespace scope from `repo_url`, ensure the target `ci-<scope>` namespace exists, and `argo submit` the kpack CI pipeline ClusterWorkflowTemplate into that namespace.
- Args:
  - `repo_url`
  - `revision`
  - `app_name`
  - `git_ref`
  - `git_provider` (`github|azure|ado`)
  - `git_creds_secret`
- Required env:
  - `REGISTRY_SERVER` (may be empty; passed through as `registry_server` workflow parameter)

#### harbor_create_project.sh

- Purpose: Create a Harbor project via the Harbor v2 API (idempotent: 409 is treated as already exists).
- Args:
  - `project_name`
  - `registry_visibility` (`public|private`)
- Required env:
  - `REGISTRY_SERVER`
  - `HARBOR_USERNAME`
  - `HARBOR_PASSWORD`
