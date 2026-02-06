# Luban CI

Luban CI is a GitOps-based Continuous Integration system running on Kubernetes, leveraging Argo Workflows and Cloud Native Buildpacks (CNB) for creating secure, compliant container images.

## Features

- **Kubernetes-Native**: Runs entirely on Kubernetes (Argo Workflows).
- **GitOps**: Pipeline definitions and configuration managed as code.
- **Cloud Native Buildpacks (CNB)**:
  - **kpack**: Kubernetes-native build service.
- **Secure**:
  - Non-root container execution (UID 1000).
  - Minimal base images (Amazon Linux 2023 Minimal).
- **Python Support**: Custom buildpack for Python with `uv` for fast dependency management.
  - Supports custom `uv` version via `.uv-version` file.

## Naming Conventions & Architecture

Luban CI enforces strict naming conventions to simplify configuration and ensure consistency across the platform.

### Relationship Map (GitHub Example)

| Concept | Naming Pattern | Example (Organization: `metasync`) |
| :--- | :--- | :--- |
| **Git Organization** | `<org>` | `metasync` |
| **Source Code Repo** | `<org>/<app-name>` | `metasync/cart-service` |
| **GitOps Repo** | `<org>/<app-name>-gitops` | `metasync/cart-service-gitops` |
| **Registry Namespace** | `<org>` | `metasync` (e.g., `harbor.io/metasync/cart-service`) |
| **ArgoCD Project** | `<env>-<project-name>` | `snd-payment` (where `payment` is the Team/Project) |
| **ArgoCD Application** | `<env>-<app-name>` | `snd-cart-service` |

### Environment Mapping

- **Sandbox (`snd`)**:
  - The default build and deployment environment.
  - **All** CI pipelines (from `main` branch, feature branches, or tags) run in the `snd-<project>` namespace.
  - Automatically deploys to the `snd` environment overlay.
- **Production (`prd`)**:
  - The release environment.
  - **No** CI builds occur directly in Production namespaces.
  - Deploys happen via **Promotion** (copying a verified image tag from `snd` to `prd`).

## Development & Release Model

Luban CI follows a **Trunk-Based Development** model with **Promotion-Based Releases**.

### 1. Development (Continuous Integration)
- **Trigger**: Commit to any branch (e.g., `main`, `feat/login`).
- **Action**:
  1.  **Dispatch**: The `luban-ci` dispatcher triggers a pipeline in the project's Sandbox namespace (`snd-<project>`).
  2.  **Build**: kpack builds the container image in Sandbox.
  3.  **Deploy**: The pipeline updates the **Sandbox** overlay in the GitOps repository.
  4.  **Verify**: The application is deployed to the Sandbox cluster for verification.

### 2. Release (Continuous Delivery)
- **Trigger**: Git Tag (e.g., `v1.0.0`) OR Manual Promotion.
- **Action**:
  1.  **Build**: Tags are also built and deployed to **Sandbox** first to ensure the exact artifact is verified.
  2.  **Promote**: A separate **Promotion Workflow** is triggered (manually or via automation).
  3.  **Deploy**: The Promotion Workflow:
      - Reads the verified image tag from the Sandbox environment.
      - Updates the **Production** overlay in the GitOps repository.
      - Creates a Pull Request (or auto-merges) to apply changes to Production.

### Why this model?
- **Build Once, Deploy Many**: The exact image tested in Sandbox is promoted to Production. We do not rebuild for Production.
- **Isolation**: Heavy build workloads run only in Sandbox/CI namespaces, keeping Production clusters stable and clean.
- **Safety**: Production deployments are explicit promotion actions, not side-effects of a merge.

### Notes
- **Labels**: Managed centrally via Kustomization to ensure consistency.
- **Gateway**: Applications use the shared `luban-gateway` in the `gateway` namespace.

## Prerequisites

- **Kubernetes Cluster**: OrbStack (recommended for local) or any K8s cluster.
  - *Note: kpack must be installed on the cluster (managed by `luban-bootstrapper`).*
- **Tools**:
  - `kubectl`
  - `pack` CLI
  - `make`
- **Accounts**:
  - GitHub Account (for source code)
  - Quay.io Account (for container registry)

## Setup

1.  **Credentials**
    - Create a `secrets/` directory for local environment files (never commit these):
      ```bash
      mkdir secrets
      ```
    - Add environment files:
      - `secrets/github.env`
        ```bash
        GITHUB_USERNAME=your_user
        GITHUB_TOKEN=your_token
        ```
      - `secrets/quay.env`
        ```bash
        QUAY_USERNAME=your_org+robot
        QUAY_PASSWORD=your_token
        ```
    - **Cloudflare Tunnel (Optional)**: If you want to expose the webhook to the public internet using a tunnel.
      - The setup script `make tunnel-setup` (detailed in [Development & Testing](#development--testing)) will handle authentication and setup.

    - The Makefile automatically loads all `secrets/*.env` files. Running `make secrets` applies them into Kubernetes as sealed credentials.
    - Ensure your VCS ignores these files. Recommended `.gitignore` entry:
      ```
      secrets/
      ```

2.  **Initialize Secrets**:
    Apply credentials to the Kubernetes cluster:
    ```bash
    make secrets
    ```

3.  **Build and Push Stack**:
    Build the custom stack (Base/Run/Build images) and push the Run image to Quay.io:
    ```bash
    make stack-build
    make stack-push
    ```

4.  **Create and Push Builder**:
    Create the CNB Builder and push it to Quay.io:
    ```bash
    make builder-build
    make builder-push
    ```

5.  **Deploy Pipeline Infrastructure**:
    Set up ServiceAccounts and RBAC for Argo Workflows:
    ```bash
    make pipeline-deploy
    ```

## Project & Application Setup

### Luban Project Setup (Team/Domain Level)
This Master Workflow initializes the infrastructure for a new Team or Domain.
- **Template**: [luban-project-workflow-template.yaml](manifests/luban-project-workflow-template.yaml)
- **What it does**:
  1.  **Harbor Project**: Creates a container registry project (e.g., `payment`) to store images.
  2.  **ArgoCD Projects**: Creates AppProjects for each environment (e.g., `snd-payment`, `prd-payment`) to manage permissions and resource whitelists.
  3.  **Namespaces**: Creates the Kubernetes namespaces for the environments.
- **Parameters**:
  - `project_name`: (Required) The name of the team or domain (e.g., `payment`).
  - `environments`: (Optional) List of environments to setup (default: `["snd", "prd"]`).
  - `git_organization`: (Optional) The GitHub Org/User where source code lives.
  - `developer_groups`: (Optional) OIDC groups for read/write access.
  - `admin_groups`: (Optional) OIDC groups for admin access.
  - `create_test_users`: (Optional) Create local ServiceAccounts (`test-project-admin`, `test-project-developer`) for verifying permissions (default: `no`).

### User Access Management
Luban CI automatically configures RBAC for your project namespaces to enable OIDC group access to the Argo Workflows UI.

- **Admin Access**:
  - Groups defined in `admin_groups` are bound to the `admin` ClusterRole within the project namespace.
  - Can view, submit, resubmit, and delete workflows.
  - Can view logs and artifacts.
- **Developer Access**:
  - Groups defined in `developer_groups` are bound to the `edit` ClusterRole within the project namespace.
  - Can view, submit, and resubmit workflows.
  - Can view logs.

**Test Users**:
If you set `create_test_users: "yes"` when creating a project, the system will provision two ServiceAccounts in each environment namespace (e.g., `snd-payment`):
1.  `test-project-admin`: Has the same permissions as your admin OIDC groups.
2.  `test-project-developer`: Has the same permissions as your developer OIDC groups.

You can use these accounts to verify permissions using `kubectl auth can-i`:
```bash
# Verify Admin Access
kubectl auth can-i delete workflow --as=system:serviceaccount:snd-payment:test-project-admin -n snd-payment
# > yes

# Verify Developer Access (cannot delete)
kubectl auth can-i delete workflow --as=system:serviceaccount:snd-payment:test-project-developer -n snd-payment
# > no
```

### Luban App Setup (Service Level)
This Workflow bootstraps a new microservice within an existing Project/Team.
- **Template**: [luban-app-workflow-template.yaml](manifests/luban-app-workflow-template.yaml)
- **What it does**:
  1.  **GitOps Repository**:
      - Provisions a new Git repository named `<app_name>-gitops` (e.g., `cart-service-gitops`).
      - Uses the standard `luban-gitops-template` (Cookiecutter).
      - Pushes the initial state to GitHub (branches: `main`, `develop`).
  2.  **ArgoCD Application**:
      - Creates an ArgoCD Application resource pointing to the new GitOps repo.
      - Connects it to the correct ArgoCD Project (e.g., `snd-payment`).
- **Parameters**:
  - `project_name`: (Required) The name of the team/domain this app belongs to (e.g., `payment`).
  - `app_name`: (Required) The name of the service (e.g., `cart-service`).
  - `git_organization`: (Optional) Auto-detected if not provided.
  - `setup_source_repo`: (Optional) Whether to provision the source code repository (`yes`, `no`). Default: `yes`.
  - `gitops_provisioner_image`: (Internal) The image used to render templates (default: `quay.io/luban-ci/gitops-provisioner:0.1.11`).

### Environment Promotion
To promote an application from `snd` to `prd`, use the `luban-promotion-template`:
- **Workflow**: `luban-promotion-template`
- **Parameters**:
  - `project_name`: (Required) Name of the project.
  - `app_name`: (Required) Name of the application.
  - `git_organization`: (Optional) Auto-detected if not provided.
  - `git_provider`: (Optional) `github` (default) or `gitlab`.

This workflow:
1.  Extracts the currently deployed image tag from the **Sandbox** overlay.
2.  Updates the **Production** overlay with that tag.
3.  Creates a Pull Request (or commits directly) to the GitOps repository to apply the change.

> **Note**: This ensures that only artifacts that have been successfully deployed and verified in Sandbox can be promoted to Production.

### Run CI Pipeline
Trigger the end-to-end CI pipeline (Checkout -> Build -> Push):
```bash
make pipeline-run
```

### Registry Configuration
- Default registry_server and image_pull_secret are managed in the `luban-config` ConfigMap.
- Override per run by passing parameters to the workflow or environment variables used by the Makefile.

### Configuration Management
- **`luban-config` ConfigMap**: Central configuration for all workflows.
  - Located in `manifests/luban-config.yaml`.
  - Keys:
    - `registry_server`: Domain of the registry (e.g., `harbor.luban.metasync.cc`).
    - `image_pull_secret`: Name of the secret for pulling images (e.g., `harbor-ro-creds`).
    - `default_image_name`: Placeholder image name (e.g., `quay.io/luban-ci/luban-hello-world-py`).
    - `default_image_tag`: Placeholder image tag (e.g., `latest`).
    - `default_container_port`: Default app port (e.g., `8000`).
    - `default_service_port`: Default service port (e.g., `80`).
    - `domain_suffix`: Suffix for app ingress (e.g., `apps.metasync.cc`).

### Global Defaults & Security
- **Global Configuration**: Managed via `argo-workflows-workflow-controller-configmap`.
- **Security Context**:
  - `runAsNonRoot: true`
  - `runAsUser: 1000`
  - `fsGroup: 1000`
- **Resource Management**:
  - `activeDeadlineSeconds`: 3600 (1 hour timeout per workflow)
  - `podGC`: `OnPodCompletion`

### Application Deployment Configuration

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

### GitOps CLI Tooling & Robustness
- **Internal Logic**: To ensure reliability across different Argo controller versions, all complex parameter derivation (e.g., extracting organization from URL, constructing GitOps repo paths) has been moved from Argo expressions into native shell scripts within the task containers.
- **Tooling Image**: To avoid installing git and yq on every workflow run, build and push a small tooling image (gitops-utils):
  ```bash
  make tools-image-build
  make tools-image-push
  ```
- **Usage**: The workflow uses a parameter `gitops_utils_image` (default: `quay.io/luban-ci/gitops-utils:0.3.3`) for checkout/update/provisioning steps.

### Concurrency Control
- Recommended: Argo Workflows Semaphores
  - A ConfigMap defines a named semaphore and its limit. This repo includes [argo-semaphore.yaml](manifests/argo-semaphore.yaml) with kpack-builds: "10".
  - The CI WorkflowTemplate references this semaphore via `spec.synchronization.semaphore.configMapKeyRef`.
  - Increase or decrease `kpack-builds` in the ConfigMap to control how many workflows (and thus kpack builds) run concurrently.
- Optional: Workflow spec.parallelism
  - Limits concurrent nodes within a single workflow. Our pipeline is sequential, so this is less impactful.
  - For parallel DAG/steps, set `spec.parallelism` in the Workflow/WorkflowTemplate.

### Workflow Cleanup
- **Global TTL Strategy**: All workflows are automatically cleaned up by the Argo Controller.
  - Successful workflows: Deleted after 30 minutes.
  - Failed/Completed workflows: Deleted after 24 hours.
- **Pod GC**: Pods are deleted immediately upon completion (`OnPodCompletion`) to free up cluster resources.

## Development & Testing

Luban CI provides a set of `test-` prefixed make targets to facilitate development and testing of the CI pipelines and event triggers.

### Trigger CI Pipeline
Manually trigger the kpack CI workflow (via Argo CLI) with custom parameters.
```bash
# Default parameters (from test/Makefile.env)
make test-ci-pipeline

# Override parameters
make test-ci-pipeline APP_NAME=my-app REPO_URL=https://github.com/myorg/my-app.git TAG=v2.0.0
```

### Simulate Webhook Event
Send a signed GitHub push event payload to the local Gateway to verify the entire event-to-pipeline flow.

**Prerequisites**:
1.  Gateway is running (`luban-gateway` in `gateway` namespace).
2.  Webhook secret is configured (`make events-webhook-secret`).
3.  Gateway URL is accessible (default: `https://webhook.luban.metasync.cc/push`).

**Cloudflare Tunnel (Optional)**:
If you need to expose the internal webhook service to the internet (e.g., for real GitHub webhooks), you can use the built-in Cloudflare Tunnel setup. The script will guide you through authentication if needed.

```bash
# Setup Tunnel
make tunnel-setup

# Setup with custom hostname
make tunnel-setup TUNNEL_HOSTNAME=my-webhook.metasync.cc
```

**Usage**:
```bash
# Option 1: Python script (requires python3)
make test-events-webhook-py

# Option 2: Shell script (requires curl, openssl)
make test-events-webhook

# Testing with custom Tunnel Hostname
export GATEWAY_URL=https://my-webhook.metasync.cc/push
make test-events-webhook
```

Both commands support environment variable overrides:
```bash
make test-events-webhook APP_NAME=my-app TAG=v1.2.3
```

### Check Build Logs
View the logs of the latest kpack build for a specific application:
```bash
make pipeline-logs APP_NAME=my-app
```

## Directory Structure

- `buildpacks/`: Custom Buildpacks source code (e.g., `python-uv`).
- `stack/`: Dockerfiles for Base, Run, and Build images.
- `manifests/`: Kubernetes manifests (Argo Workflows, RBAC).
- `tools/`: Utility tools (GitOps provisioner, CLI utils).
- `test/`: Test scripts and Makefile.
- `Makefile`: Main entry point for all operations.
