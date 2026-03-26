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
    - `github_server`: GitHub server hostname (default: `github.com`).
    - `azure_server`: Azure DevOps server hostname (default: `dev.azure.com`).
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

### Git Provider Configuration (Azure DevOps)
If you are using Azure DevOps instead of GitHub:
1.  **Organization & Project**: Ensure your Azure DevOps Organization exists. The `luban-project-workflow` will create the Project for you.
2.  **Personal Access Token (PAT)**:
    - Scopes required: `Code (Read & Write)`, `Project and Team (Read & Write)`, `Work Items (Read & Write)`.
    - Configure in `secrets/*.env` (exporting `AZURE_DEVOPS_TOKEN` and `AZURE_ORGANIZATION`, mapped to the `azure-creds` secret).
3.  **Environment Variables**:
    - Ensure `AZURE_SERVER` is available in the environment if using a self-hosted Azure DevOps Server.
    - Default is `dev.azure.com`.

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
  - The CI kpack ClusterWorkflowTemplate references this semaphore via `spec.synchronization.semaphore.configMapKeyRef`.
  - Increase or decrease `kpack-builds` in the tenant namespace ConfigMap to control how many kpack builds run concurrently.
- **Optional**: Workflow spec.parallelism
  - Limits concurrent nodes within a single workflow. Our pipeline is sequential, so this is less impactful.
  - For parallel DAG/steps, set `spec.parallelism` in the Workflow/WorkflowTemplate.

## Workflow Cleanup
- **Template TTL Strategy**: Most workflows set `spec.ttlStrategy` explicitly.
  - For `luban-ci-kpack-template`, pods are retained until workflow deletion (`podGC: OnWorkflowDeletion`) and workflows are deleted after a delay (success cleans up faster than failures).
  - If you change retention/TTL, prefer updating the specific WorkflowTemplate/ClusterWorkflowTemplate rather than relying on controller defaults.
