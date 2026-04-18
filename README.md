# Luban CI

Luban CI is a GitOps-based Continuous Integration system running on Kubernetes, leveraging Argo Workflows and Cloud Native Buildpacks (CNB) for creating secure, compliant container images.

## Features

- **Kubernetes-Native**: Runs entirely on Kubernetes (Argo Workflows).
- **GitOps**: Pipeline definitions and configuration managed as code.
- **Cloud Native Buildpacks (CNB)**: Kubernetes-native build service (kpack).
- **Secure**: Non-root execution, minimal base images.
- **Python Support**: Custom buildpack for Python with `uv` for fast dependency management.
- **Dagster Support**: Full platform provisioning and isolated Code Locations.

## Documentation

### Core Concepts (The "Why")
- [**CI/CD Philosophy**](docs/concepts/cicd-philosophy.md): Understanding Trunk-Based Development and Promotion-Based Releases.
- [**Environment Promotion**](docs/concepts/environment-promotion.md): How "Build Once, Promote Anywhere" works (SND -> PRD).
- [**GitOps Architecture**](docs/concepts/gitops-architecture.md): Naming conventions, project structure, and repo organization.
- [**Dagster Integration**](docs/guides/dagster-integration.md): Architecture for Data Platforms and Code Locations.

### User Guides (The "How-To")
- [**Getting Started**](docs/guides/getting-started.md): Installation, prerequisites, and initial setup.
- [**Developer Workflow**](docs/guides/developer-workflow.md): How to trigger pipelines, check logs, and manage permissions.
- [**Admin Guide**](docs/guides/admin-guide.md): Configuration, security, resource management, and troubleshooting.

### Architecture
- [**Multi-Cluster v2**](docs/architecture/multi-cluster-v2.md): Admin cluster vs worker clusters, centralized infra repos, and `cluster_map` routing.

### Project Docs
- [Roadmap](docs/ROADMAP.md)
- [Requirements](docs/requirements.md)

## Directory Structure

- `buildpacks/`: Custom Buildpacks source code (e.g., `python-uv`).
- `stack/`: Dockerfiles for Base, Run, and Build images.
- `manifests/`: Kubernetes manifests (Argo Workflows, RBAC).
- `tools/`: Utility tools (Luban provisioner, GitOps utils).
- `test/`: Test scripts and Makefile.
- `docs/`: Documentation.
- `Makefile`: Main entry point for all operations.

## Quick Start

1.  **Install Prerequisites**: `kubectl`, `pack`, `make`.
2.  **Setup Credentials**: Create `secrets/` with GitHub/Azure tokens (see [Getting Started](docs/guides/getting-started.md)).
3.  **Deploy Pipeline**: `make pipeline-deploy`.
4.  **Create Project**: Run the Project Setup Workflow to initialize namespaces and RBAC.

For detailed instructions, see the [Getting Started Guide](docs/guides/getting-started.md).
