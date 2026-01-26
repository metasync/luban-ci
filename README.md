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

### GitOps CLI Tooling
- To avoid installing git and yq on every workflow run, build and push a small tooling image (gitops-utils):
  ```bash
  make tools-image-build
  make tools-image-push
  ```
- The workflow uses a parameter `gitops_cli_image` (default: quay.io/luban-ci/gitops-utils:0.1.0) for checkout/update steps. Override if needed.

### Concurrency Control
- Recommended: Argo Workflows Semaphores
  - A ConfigMap defines a named semaphore and its limit. This repo includes [argo-semaphore.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argo-semaphore.yaml) with kpack-builds: "2".
  - The CI WorkflowTemplate references this semaphore via `spec.synchronization.semaphore.configMapKeyRef`.
  - Increase or decrease `kpack-builds` in the ConfigMap to control how many workflows (and thus kpack builds) run concurrently.
- Optional: Workflow spec.parallelism
  - Limits concurrent nodes within a single workflow. Our pipeline is sequential, so this is less impactful.
  - For parallel DAG/steps, set `spec.parallelism` in the Workflow/WorkflowTemplate.

### Argo Project Setup
- A WorkflowTemplate is provided to create Argo CD AppProjects dynamically:
  - Template: [argocd-project-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argocd-project-workflow-template.yaml)
  - Parameters:
    - project_name: required (domain/team name)
    - environments: optional array, default ["snd", "prd"]
    - source_repos: optional array, default ["https://github.com/metasync/*"]
    - developer_groups: optional array (OIDC group names), default []
    - admin_groups: optional array (OIDC group names), default []
  - Creates AppProject named "<environment>-<project_name>" in namespace "argocd" with destinations and whitelists matching the devops baseline.
  - Configures roles:
    - project-developer: read/sync access, mapped to developer_groups
    - project-admin: full access, mapped to admin_groups

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
- `Makefile`: Main entry point for all operations.
