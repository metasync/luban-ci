# Luban CI

Luban CI is a GitOps-based Continuous Integration system running on Kubernetes, leveraging Argo Workflows and Cloud Native Buildpacks (CNB) for creating secure, compliant container images.

## Features

- **Kubernetes-Native**: Runs entirely on Kubernetes (Argo Workflows).
- **GitOps**: Pipeline definitions and configuration managed as code.
- **Cloud Native Buildpacks (CNB)**:
  - **kpack (Recommended)**: Kubernetes-native build service.
  - **pack (Legacy)**: Supports Docker-in-Docker (DinD) execution.
- **Secure**:
  - Non-root container execution (UID 1000).
  - Minimal base images (Amazon Linux 2023 Minimal).
  - Docker-in-Docker (DinD) or Docker-out-of-Docker (DooD) support.
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

1.  **Credentials**:
    Create a `secrets/` directory and add your credentials:
    ```bash
    mkdir secrets
    # Copy examples (if available) or create files manually
    ```
    
    `secrets/github.env`:
    ```bash
    GITHUB_USERNAME=your_user
    GITHUB_TOKEN=your_token
    ```

    `secrets/quay.env`:
    ```bash
    QUAY_USERNAME=your_org+robot
    QUAY_PASSWORD=your_token
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
*Note: This defaults to the kpack workflow (`pipeline-run-kpack`). Use `make pipeline-run-dind` for the DinD version.*

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
