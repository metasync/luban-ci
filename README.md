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
  - Tracks the `develop` branch of the GitOps repository.
  - Deploys to the `<snd>-<project>` namespace (e.g., `snd-payment`).
- **Production (`prd`)**:
  - Tracks the `main` branch of the GitOps repository.
  - Deploys to the `<prd>-<project>` namespace (e.g., `prd-payment`).

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
    - The Makefile automatically loads all `secrets/*.env` files. Running `make secrets` applies them into Kubernetes as sealed credentials.
    - Ensure your VCS ignores these files. Recommended `.gitignore` entry:
      ```
      secrets/
      ```

2.  **Fix DNS (OrbStack only)**:
    If running on OrbStack, patch CoreDNS to resolve local ingress domains:
    ```bash
    make fix-dns
    ```

3.  **Configure Kpack TLS (OrbStack only)**:
    Configure Kpack to trust the local Harbor certificate authority:
    ```bash
    make configure-kpack
    ```

4.  **Initialize Secrets**:
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

## Usage

### Run CI Pipeline
Trigger the end-to-end CI pipeline (Checkout -> Build -> Push):
```bash
make pipeline-run
```

### GitOps Branch Strategy
- Sandbox (snd) tracks the develop branch in the per-app GitOps repo.
- Production (prd) tracks the main branch; promotion is via PR that bumps app/overlays/prd/kustomization.yaml newTag.
- CI updates app/overlays/snd/kustomization.yaml newTag in develop to the tag (if present) or the commit revision.

### Registry Configuration
- Default registry_server is quay.io, registry_namespace is luban-ci.
- Override per run by passing parameters to the workflow or environment variables used by the Makefile.

### Application Deployment Configuration
- **Start Command**: The `python-uv` buildpack does not set a default start command. You must specify the command in your Kubernetes Deployment manifest.
- **Using `args` vs `command`**: It is **strongly recommended** to use `args` (which corresponds to Docker `CMD`) instead of `command` (Docker `ENTRYPOINT`).
  - Using `args` allows the CNB Launcher (the default entrypoint) to run first. The Launcher sets up the runtime environment (including adding `uv` to `PATH`) before executing your arguments.
  - Example:
    ```yaml
    containers:
      - name: app
        image: quay.io/my-org/my-app:latest
        args: ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0"]
    ```

### GitOps CLI Tooling
- To avoid installing git and yq on every workflow run, build and push a small tooling image (gitops-utils):
  ```bash
  make tools-image-build
  make tools-image-push
  ```
- The workflow uses a parameter `gitops_utils_image` (default: quay.io/luban-ci/gitops-utils:0.3.3) for checkout/update steps. Override if needed.

### Concurrency Control
- Recommended: Argo Workflows Semaphores
  - A ConfigMap defines a named semaphore and its limit. This repo includes [argo-semaphore.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argo-semaphore.yaml) with kpack-builds: "2".
  - The CI WorkflowTemplate references this semaphore via `spec.synchronization.semaphore.configMapKeyRef`.
  - Increase or decrease `kpack-builds` in the ConfigMap to control how many workflows (and thus kpack builds) run concurrently.
- Optional: Workflow spec.parallelism
  - Limits concurrent nodes within a single workflow. Our pipeline is sequential, so this is less impactful.
  - For parallel DAG/steps, set `spec.parallelism` in the Workflow/WorkflowTemplate.

## Project & Application Setup

### Luban Project Setup (Team/Domain Level)
This Master Workflow initializes the infrastructure for a new Team or Domain.
- **Template**: [luban-project-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/luban-project-workflow-template.yaml)
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

### Luban App Setup (Service Level)
This Workflow bootstraps a new microservice within an existing Project/Team.
- **Template**: [luban-app-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/luban-app-workflow-template.yaml)
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
  - `gitops_provisioner_image`: (Internal) The image used to render templates (default: `quay.io/luban-ci/gitops-provisioner:0.1.5`).

### Workflow Cleanup
- A CronWorkflow runs every 15 minutes to delete completed workflows (Succeeded, Failed, Error) to reclaim resources.
- Manifest: [workflow-cleanup-cron.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/workflow-cleanup-cron.yaml)
- Deployed automatically with `make pipeline-deploy`.

### Webhook Trigger
The pipeline is configured to run automatically on GitHub push events via the `luban-gateway`.
To test locally (simulate webhook):

1.  Ensure the Gateway is running (managed by `luban-bootstrapper`) and `luban-ci` listener is active.
2.  Run the webhook test command:
    ```bash
    make events-webhook-test
    ```
    This script (`test/webhook_test.py`) will:
    - Retrieve the shared webhook secret from Kubernetes.
    - Construct a valid GitHub push event payload (defaulting to `v0.1.0` tag).
    - Sign the payload with HMAC-SHA256.
    - Send the request to `https://webhook.luban.k8s.orb.local/push` via the Gateway.

Watch the workflow status:
```bash
kubectl get wf -n luban-ci -w
```

### Check Build Logs
View the logs of the latest kpack build:
```bash
make pipeline-logs
```

### Test Result
Verify the pushed application image locally:
```bash
make test
```

## Directory Structure

- `buildpacks/`: Custom Buildpacks source code (e.g., `python-uv`).
- `stack/`: Dockerfiles for Base, Run, and Build images.
- `manifests/`: Kubernetes manifests (Argo Workflows, RBAC).
- `tools/`: Utility tools (GitOps provisioner, CLI utils).
- `Makefile`: Main entry point for all operations.
