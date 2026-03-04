# GitOps Architecture

Luban CI enforces strict naming conventions and a GitOps-based architecture to simplify configuration and ensure consistency across the platform.

## Naming Conventions

| Concept | Naming Pattern | Example (Organization: `metasync`) |
| :--- | :--- | :--- |
| **Git Organization** | `<org>` | `metasync` |
| **Source Code Repo** | `<org>/<app-name>` | `metasync/cart-service` |
| **GitOps Repo** | `<org>/<app-name>-gitops` | `metasync/cart-service-gitops` |
| **Registry Namespace** | `<org>` | `metasync` (e.g., `harbor.io/metasync/cart-service`) |
| **ArgoCD Project** | `<env>-<project-name>` | `snd-payment` (where `payment` is the Team/Project) |
| **ArgoCD Application** | `<env>-<app-name>` | `snd-cart-service` |

## GitOps Branching Strategy

Luban CI uses a multi-branch GitOps strategy to map Git branches to Kubernetes environments.

| Branch | Environment | Purpose | Update Mechanism |
| :--- | :--- | :--- | :--- |
| `develop` | **Sandbox (`snd`)** | Integration testing, validation of latest builds. | **Automated**: The CI pipeline commits directly to this branch after a successful build. |
| `main` | **Production (`prd`)** | Stable release environment. | **Promotion**: A Pull Request merges verified changes (including `base` manifests) from `develop` to `main`, and updates the image tag in `overlays/prd`. |

### Why Multi-Branch?
- **Isolation**: Changes in `develop` (Sandbox) do not affect Production until explicitly promoted.
- **History**: The `main` branch history reflects only stable releases deployed to Production.
- **Access Control**: You can apply stricter branch protection rules to `main` (e.g., requiring approval) while allowing CI automation to commit to `develop`.

### Repository Structure
The GitOps repository (`<app-name>-gitops`) is structured using Kustomize overlays:

```text
├── app
│   ├── base                   # Base manifests (Deployment, Service, etc.)
│   └── overlays
│       ├── snd                # Sandbox-specific configuration (replicas, resources, image tags)
│       │   ├── kustomization.yaml
│       │   └── patch-replicas.yaml
│       └── prd                # Production-specific configuration
│           ├── kustomization.yaml
│           └── patch-replicas.yaml
```

- **Sandbox Deployment**: ArgoCD tracks the `develop` branch and applies `app/overlays/snd`.
- **Production Deployment**: ArgoCD tracks the `main` branch and applies `app/overlays/prd`.

## Project Setup (Team Level)

The **Luban Project Setup** workflow initializes the infrastructure for a new Team or Domain.

- **Template**: [luban-project-workflow-template.yaml](../../manifests/workflows/luban-project-workflow-template.yaml)
- **Actions**:
  1.  **Harbor Project**: Creates a container registry project to store images.
  2.  **ArgoCD Projects**: Creates AppProjects for each environment (e.g., `snd-payment`, `prd-payment`).
  3.  **Namespaces**: Creates the Kubernetes namespaces for the environments.
- **Key Parameters**: `project_name`, `admin_group`, `developer_group`.

## Application Setup (Service Level)

The **Luban App Setup** workflow bootstraps a new microservice within an existing Project.

- **Template**: [luban-app-workflow-template.yaml](../../manifests/workflows/luban-app-workflow-template.yaml)
- **Actions**:
  1.  **GitOps Repository**:
      - Provisions a new Git repository named `<app_name>-gitops`.
      - Uses the standard `luban-gitops-template` (Cookiecutter).
      - Pushes the initial state to GitHub (branches: `main`, `develop`).
  2.  **ArgoCD Application**:
      - Creates an ArgoCD Application resource pointing to the new GitOps repo.
      - Connects it to the correct ArgoCD Project.
- **Key Parameters**: `project_name`, `app_name`, `environment`.
