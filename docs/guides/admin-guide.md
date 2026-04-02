# Admin Guide

This guide covers the administration and configuration of the Luban CI platform.

## Configuration Management

- **`luban-config` ConfigMap**: Central configuration for all workflows.
  - Located in `manifests/config/luban-config.yaml`.
  - Keys:
    - `domain_suffix`: Suffix for app ingress hostnames (e.g., `apps.metasync.cc`).
    - `registry_server`: Domain of the registry (e.g., `harbor.luban.metasync.cc`).
    - `image_pull_secret`: Name of the secret for pulling images (e.g., `harbor-ro-creds`).
    - `webhook_url`: Public webhook endpoint for the event gateway.
    - `cluster_map`: JSON map of `deploy_env` -> Kubernetes cluster URL (e.g., `snd`/`prd`).
    - `cilium_egress_gateway_policy`: (Optional) Shared `CiliumEgressGatewayPolicy` name for CI egress IP control.
    - `github_server`: GitHub server hostname (default: `github.com`).
    - `azure_server`: Azure DevOps Services (cloud) host used for REST API calls (default: `dev.azure.com`).
    - `ado_server`: Azure DevOps Server (on-prem) host used for REST API calls (required when `git_provider=ado`).
    - `azure_devops_api_version`: Azure DevOps Services REST API version (default: `7.1`).
    - `ado_devops_api_version`: Azure DevOps Server REST API version (default: `7.1`).
    - `luban_provisioner_image`: Container image for `luban-provisioner`.
    - `gitops_utils_image`: Container image for GitOps utility tools.
    - `python_index_url`: (Optional) Custom Python Package Index URL for project scaffolding.
    - `python_index_name`: (Optional) Name/alias for the custom index.
    - `uv_release_base_url`: (Optional) Base URL for `uv` release assets + `.sha256`.
    - `uv_python_install_mirror`: (Optional) Base URL for `uv` managed Python downloads.

- **`luban-python-config` ConfigMap**: Defaults used when provisioning Python projects.
  - Located in `manifests/config/luban-python-config.yaml`.
  - Keys:
    - `container_port`, `service_port`
    - `default_image_name`, `default_image_tag`
    - `template_type`

- **`luban-dagster-config` ConfigMap**: Defaults used when provisioning Dagster projects.
  - Located in `manifests/config/luban-dagster-config.yaml`.
  - Keys:
    - `platform_port`, `code_location_port`
    - `dagster_version`, `postgres_version`

### Dagster + dbt Partitioning Notes

- Daily partitions are the default and recommended granularity for data warehouse workloads.
- Partitioning is primarily for query pruning and retention management (for example, dropping data by day).
- Hourly aggregation is a common modeling pattern, but the aggregated tables are usually much smaller than the raw transactional tables and often do not need hourly partitioning.
- Hourly partitions can be useful for high-frequency, large-volume access patterns, but they add orchestration complexity and are not enabled in the current Dagster+dbt template.

### Registry Configuration
- Default `registry_server` and `image_pull_secret` are managed in the `luban-config` ConfigMap.
- Override per run by passing parameters to the workflow or environment variables used by the Makefile.

### Air-Gapped Mirrors (uv + Python)
If your cluster cannot access the public internet, configure mirrors in the `luban-config` ConfigMap:
- `uv_release_base_url`: Base URL for `uv` release assets and their `.sha256` checksum files.
- `uv_python_install_mirror`: Mirror base URL for `uv` managed Python downloads (exported as `UV_PYTHON_INSTALL_MIRROR` during builds).

These values are passed into kpack builds as build-time environment variables. If unset, the buildpack defaults remain unchanged (official upstream downloads).

#### `uv_release_base_url` layout
The buildpack constructs the download URL like:
- `${uv_release_base_url}/${UV_VERSION}/${ASSET}`
- `${uv_release_base_url}/${UV_VERSION}/${ASSET}.sha256`

Where `${ASSET}` is architecture-specific:
- `uv-x86_64-unknown-linux-musl.tar.gz`
- `uv-aarch64-unknown-linux-musl.tar.gz`

Example (x86_64, `UV_VERSION=0.10.4`):
- Tarball: `https://mirror.example.com/uv/releases/download/0.10.4/uv-x86_64-unknown-linux-musl.tar.gz`
- Checksum: `https://mirror.example.com/uv/releases/download/0.10.4/uv-x86_64-unknown-linux-musl.tar.gz.sha256`

Your mirror must host both files at the same paths for checksum verification to pass.

#### `uv_python_install_mirror` layout
`UV_PYTHON_INSTALL_MIRROR` replaces the base URL used for downloading Python distributions. The remainder of the download path is preserved.

Example from uv docs/issues (managed Python uses `python-build-standalone` releases):
- Upstream:
  - `https://github.com/indygreg/python-build-standalone/releases/download/20240713/cpython-3.12.4%2B20240713-aarch64-apple-darwin-install_only.tar.gz`
- With mirror:
  - `${UV_PYTHON_INSTALL_MIRROR}/20240713/cpython-3.12.4%2B20240713-aarch64-apple-darwin-install_only.tar.gz`

So your mirror needs to serve artifacts under:
- `${uv_python_install_mirror}/<release_id>/<artifact_filename>`

Reference: https://docs.astral.sh/uv/reference/environment/#uv_python_install_mirror

### kpack Lifecycle Image
Luban CI uses kpack to run Cloud Native Buildpacks (CNB). kpack relies on a `ClusterLifecycle` object (default: `default-lifecycle`) to determine which CNB lifecycle image to run.

For stability and reproducibility, the lifecycle image is pinned by digest in `manifests/kpack/kpack-lifecycle.yaml`. Avoid using an unpinned tag (e.g., `:latest`) because it can introduce unexpected drift.

If your cluster has slow access to `ghcr.io`, mirror the lifecycle image into your own registry and keep it pinned by digest.

### Local DNS (OrbStack / local clusters)
If you run Luban CI locally (e.g., OrbStack) and need in-cluster components (kpack, Argo, etc.) to resolve ingress-style domains such as `harbor.luban.metasync.cc`, use:

```bash
make patch-coredns
```

This patches CoreDNS `NodeHosts` to map the ingress domains to the Gateway LoadBalancer IP.

### GitOps Branch Behavior
The `luban-ci-kpack` pipeline updates the application GitOps repo on `gitops_branch` (default: `develop`).
- If the branch exists remotely, it checks it out.
- If it does not exist, it creates the branch and pushes it (requires write access).

### Cilium Egress Gateway (Optional)

If the cluster uses Cilium Egress Gateway and CI egress IPs are controlled by a shared `CiliumEgressGatewayPolicy`, set `cilium_egress_gateway_policy` in `luban-config`.

When this key is set, Luban labels each newly created `ci-*` namespace via Argo CD `managedNamespaceMetadata` with:

- `luban-ci.io/cilium-egress-gateway-policy=<policy-name>`

The policy should select namespaces by this label. A complete sample policy is in `docs/guides/cilium-egress-gateway.md`.

### Git Provider Configuration (Azure DevOps)

Luban supports two Azure DevOps providers:

- `git_provider=azure`: Azure DevOps Services (cloud)
- `git_provider=ado`: Azure DevOps Server (on-prem)

If you are using Azure DevOps instead of GitHub:
1. **Organization & Project**: Ensure your Azure DevOps Organization exists. The `luban-project-workflow` will create the Project for you.
2. **Personal Access Token (PAT)**:
   - Scopes required: `Code (Read & Write)`, `Project and Team (Read & Write)`, `Work Items (Read & Write)`.
   - Configure in `secrets/*.env` (exporting `AZURE_DEVOPS_TOKEN` and `AZURE_ORGANIZATION`, mapped to the `azure-creds` secret).
3. **Environment Variables**:
   - For Azure DevOps Server (on-prem), set `ado_server` (and optionally `ado_base_url`) in `manifests/config/luban-config.yaml`, and provide `ado-creds` (`ADO_DEVOPS_TOKEN`).
   - Set `azure_devops_api_version` (cloud) and/or `ado_devops_api_version` (on-prem) in `manifests/config/luban-config.yaml`.
   - For ArgoCD repo credentials on ADO Server, also set `ADO_COLLECTION` (used to build the repo-creds URL).

For kpack builds using SSH on Azure DevOps Server, ensure `ado-ssh-creds` in each `ci-*` namespace has `kpack.io/git` set to the SSH clone host.
This is typically the same host as `ado_server`, and can be overridden during infra init via `ADO_SSH_HOST` / `--ado-ssh-host`.

### Argo CD Destinations (Multi-Cluster)

Argo CD Projects and Applications must agree on which Kubernetes cluster a given environment deploys to.

- `luban-config.cluster_map` defines the destination cluster URL per environment (for example `snd` and `prd`).
- `argocd-app-setup-template` uses `cluster_map` to set `Application.spec.destination.server`.
- `argocd-project-setup-template` uses `cluster_map` to set the `AppProject.spec.destinations[].server` allowlist.

If these drift, Argo CD may reject application syncs due to destination not being permitted by the AppProject.

### Azure DevOps URL Parsing (Dispatcher + GitOps)

Luban derives CI routing and GitOps repo locations from Azure DevOps repository URLs.

**Namespace derivation (webhook dispatcher)**

The `luban-ci-dispatch` workflow derives the tenant CI namespace from the Azure DevOps *project*.

- Input: the webhook `remoteUrl` (passed as `repo_url`)
- Rule (HTTPS URLs): the project is the path segment immediately before `/_git/`
- Output:
  - `registry_namespace` / `namespace scope` = `<project>`
  - target CI namespace = `ci-<project>`

Examples:

- Azure DevOps Services (cloud):
  - `https://dev.azure.com/<org>/<project>/_git/<repo>`
  - derives `<project>`
- Azure DevOps Server (on-prem):
  - `https://<host>/<collection>/<project>/_git/<repo>`
  - derives `<project>` (not `<collection>`)
  - if you have a path prefix (for example `/tfs`): `https://<host>/tfs/<collection>/<project>/_git/<repo>` still derives `<project>`

This avoids coupling namespace routing to the Azure DevOps Server collection name, which is often not the tenancy boundary.

**GitOps repo URL derivation (kpack `git-update`)**

When `git_provider` is `azure` (cloud) or `ado` (on-prem), the CI pipeline updates the application GitOps repository by rewriting the repository portion of the URL:

- Input: application repo URL `.../_git/<repo>`
- Output: GitOps repo URL `.../_git/<app_name>-gitops`

For Azure DevOps Server (on-prem), this preserves the original host/collection/project path so the pipeline does not hardcode `dev.azure.com`.

Notes:

- The convention assumes the GitOps repo is named `<app_name>-gitops`.
- The `build-push` step normalizes `repo_url` to an SSH clone URL:
  - `git_provider=azure` (Azure DevOps Services): `git@ssh.dev.azure.com:v3/<org>/<project>/<repo>`
  - `git_provider=ado` (Azure DevOps Server): `git@<host>:/<collection>/<project>/_git/<repo>`
  - If you pass an SSH URL already, it is used as-is.
- Azure DevOps Server requires SSH to be enabled on the server side.

### Gateway Namespace

The `gateway` namespace hosts the shared Gateway API `Gateway` (for example `luban-gateway`). Application `HTTPRoute` resources typically live in the application namespace but attach to the shared Gateway using `parentRefs.namespace: gateway`.

### Git Authentication (Workflows + Provisioner)

- By default, workflows and `luban-provisioner` use clean HTTPS repo URLs and rely on git's credential mechanism (`credential.helper store`) for authentication.
- This avoids embedding PATs in remote URLs (which can leak via logs or `.git/config`) and works for GitHub and Azure DevOps Services (cloud).

For Azure DevOps Server (on-prem), you may need to send an explicit HTTP `Authorization: Basic <base64(username:PAT)>` header for git operations. Luban supports this via an alternate auth mode.

**Config keys (in `luban-config`)**

- `github_https_auth_mode`: recommended `credential_store`.
- `azure_https_auth_mode`: recommended `credential_store` for Azure DevOps Services (cloud).
- `ado_https_auth_mode`: recommended `extraheader_basic` for Azure DevOps Server (on-prem).
- `ado_basic_auth_username`: optional username to use when building the Basic auth header.
- `ado_base_url`: optional base URL (scheme + optional path prefix), used for Azure DevOps Server.

Notes:

- Workflows that perform git operations (including the kpack GitOps update step) use the provider-scoped `*_https_auth_mode` settings.
- Git credentials come from `*-creds` Secrets (for example `github-creds` and `azure-creds`) and include:
  - `username`
  - `token`

Common values:

- Azure DevOps Services (cloud): `7.1`
- Azure DevOps Server 2020 (on-prem): often `6.1-preview` (depending on the endpoint)

## Application Deployment Configuration

- **Start Command**: The `python-uv` buildpack supports two ways to define the start command:
  1.  **pyproject.toml (Recommended)**: If your project has a `[project.scripts]` section in `pyproject.toml`, the buildpack will automatically detect the entry point and set it as the default start command (e.g., `uv run my-app`). It supports common script names like `app` or `start`.
  2.  **Kubernetes Manifest**: You can explicitly specify the command in your Kubernetes Deployment manifest using `args`.
- **Using `args` vs `command`**: It is **strongly recommended** to use `args` (which corresponds to Docker `CMD`) instead of `command` (Docker `ENTRYPOINT`).
  - Using `args` allows the CNB Launcher (the default entrypoint) to run first. The Launcher sets up the runtime environment (including adding `uv` to `PATH`) before executing your arguments.
  - **Note**: It is preferred to specify scripts in `project.scripts` in `pyproject.toml` rather than using `args` manually.
  - Example:
    ```yaml
    containers:
      - name: app
        image: quay.io/my-org/my-app:latest
        args:
          - uv
          - run
          - uvicorn
          - main:app
          - --host
          - 0.0.0.0
    ```

## Global Defaults & Security

- **Global Configuration**: Managed via `argo-workflows-workflow-controller-configmap`.
- **Security Context**:
  - `runAsNonRoot: true`
  - `runAsUser: 1000`
  - `fsGroup: 1000`
- **Resource Management**: Prefer setting timeouts/GC per template (some workflows intentionally keep pods longer for log access).

## Concurrency Control

- **Recommended**: Argo Workflows Semaphores
  - A ConfigMap (`workflow-semaphores`) defines a named semaphore and its limit in each tenant CI namespace (`ci-*`).
  - The CI kpack ClusterWorkflowTemplate references this semaphore via `spec.synchronization.semaphores[].configMapKeyRef`.
  - Increase or decrease `kpack-builds` in the tenant namespace ConfigMap to control how many kpack builds run concurrently.
- **Optional**: Workflow spec.parallelism
  - Limits concurrent nodes within a single workflow. Our pipeline is sequential, so this is less impactful.
  - For parallel DAG/steps, set `spec.parallelism` in the Workflow/WorkflowTemplate.

## Workflow Cleanup
- **Template TTL Strategy**: Most workflows set `spec.ttlStrategy` explicitly.
  - For `luban-ci-kpack-template`, pods are retained until workflow deletion (`podGC: OnWorkflowDeletion`) and workflows are deleted after a delay (success cleans up faster than failures).
  - If you change retention/TTL, prefer updating the specific WorkflowTemplate/ClusterWorkflowTemplate rather than relying on controller defaults.
