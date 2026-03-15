# Admin Guide

This guide covers the administration and configuration of the Luban CI platform.

## Configuration Management

- **`luban-config` ConfigMap**: Central configuration for all workflows.
  - Located in `manifests/config/luban-config.yaml`.
  - Keys:
    - `registry_server`: Domain of the registry (e.g., `harbor.luban.metasync.cc`).
    - `image_pull_secret`: Name of the secret for pulling images (e.g., `harbor-ro-creds`).
    - `default_image_name`: Placeholder image name (e.g., `quay.io/luban-ci/luban-hello-world-py`).
    - `default_image_tag`: Placeholder image tag (e.g., `latest`).
    - `default_container_port`: Default app port (e.g., `8000`).
    - `default_service_port`: Default service port (e.g., `80`).
    - `domain_suffix`: Suffix for app ingress (e.g., `apps.metasync.cc`).
    - `azure_server`: (Optional) Azure DevOps server hostname (e.g., `dev.azure.com`). Required for Azure DevOps.
    - `python_index_url`: (Optional) Custom Python Package Index URL (e.g., `https://devpi.luban-ci.io/root/pypi`). If set, it will be injected into the `pyproject.toml` of new Python/Dagster projects.
    - `python_index_name`: (Optional) Name for the custom index (default: `custom`).

### Registry Configuration
- Default `registry_server` and `image_pull_secret` are managed in the `luban-config` ConfigMap.
- Override per run by passing parameters to the workflow or environment variables used by the Makefile.

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
