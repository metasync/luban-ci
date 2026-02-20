# Luban CI Requirements

## 1. Project Overview
**Project Name:** `luban-ci`
**Goal:** Build a flexible, extensible, GitOps-based Continuous Integration (CI) system.
**Platform:** Kubernetes (OrbStack for local development).
**Scope:** The underlying CI/CD platform infrastructure is assumed to be pre-provisioned by [luban-bootstrapper](https://github.com/metasync/luban-bootstrapper). `luban-ci` focuses on the *pipeline implementation*, *custom buildpack ecosystem*, and *GitOps automation*.

**Design Principles:**
*   **Extensibility:** Support for multiple Git providers (GitHub, Azure DevOps) and languages.
*   **Security:** Mandatory security defaults (non-root execution, minimal base images).
*   **GitOps:** All infrastructure and application configurations managed as code.
*   **Promotion-Based Delivery:** Strict separation between build (Sandbox) and release (Production) environments.

## 2. Infrastructure & Technology Stack
The following components are assumed available via `luban-bootstrapper`:
- **Orchestration:** Argo Workflows
- **Event Bus:** Argo Events
- **Continuous Delivery:** Argo CD
- **Build Engine:** kpack (Kubernetes-native implementation of Cloud Native Buildpacks)
- **Ingress/Gateway:** Envoy Gateway / Cloudflare Tunnel
- **Container Registry:** Quay.io (External) / Harbor (Internal)

## 3. Pipeline Architecture
The CI/CD process follows a strict GitOps workflow with modular templates.

### 3.1. Trigger Phase (Argo Events)
- **Source:** Webhooks from GitHub or Azure DevOps.
- **Mechanism:** Argo Events receives the webhook and triggers an Argo Workflow sensor.
- **Payload:** Normalizes Git metadata (commit SHA, branch, repo URL) from different providers.

### 3.2. Build Phase (Argo Workflows + kpack)
1.  **Dispatch:** A dispatcher workflow analyzes the event and triggers the pipeline in the correct project namespace.
2.  **Build (kpack):**
    -   Uses `kp` CLI to trigger a build in the kpack infrastructure.
    -   Leverages the custom Buildpack ecosystem (Python + uv).
    -   Builds are always performed in the **Sandbox** environment.
3.  **Deploy (Sandbox):**
    -   Updates the `snd` overlay in the GitOps repository.
    -   Argo CD syncs the changes to the Sandbox cluster for verification.

### 3.3. Release Phase (Promotion)
-   **Trigger:** Manual or Automated (Git Tag).
-   **Mechanism:** A separate Promotion Workflow.
-   **Action:**
    -   Reads the verified image tag from the Sandbox environment.
    -   Updates the `prd` overlay in the GitOps repository.
    -   Creates a Pull Request (GitHub/Azure) for approval.

## 4. Custom Buildpacks Ecosystem (General)
To support modern development standards and security requirements, we developed a custom Cloud Native Buildpacks stack.

### 4.1. Security & Compliance
-   **Non-Root Execution:** All applications run as UID 1000.
-   **Minimal Base Image:** Amazon Linux 2023 Minimal.
-   **SBOM:** Full Software Bill of Materials generation.

### 4.2. Stack Components
1.  **Build Image:** Amazon Linux-based build environment.
2.  **Run Image:** Minimal Amazon Linux runtime.
3.  **Trusted Builder:** Composite builder image.

## 5. Language Support: Python
-   **Dependency Manager:** `uv`.
-   **Version Management:** `.python-version` support.
-   **Compliance:** CNB Platform API compliant.

## 6. Provisioning & Tooling
A unified CLI tool (`luban-provisioner`) automates the setup of:
-   **Projects:** Namespaces, RBAC, Harbor Projects.
-   **GitOps Repositories:** ArgoCD application manifests (Base/Overlays).
-   **Source Repositories:** Application scaffolding.
-   **Provider Abstraction:** Seamless support for both GitHub and Azure DevOps.

## 7. Dagster Integration

### 7.1 Architecture Overview
Dagster is integrated as the orchestration layer for data pipeline workflows within the luban-ci ecosystem. The integration follows a GitOps approach with three distinct deployment patterns:

- **Platform GitOps:** Core Dagster infrastructure managed centrally
- **Code Location Source:** Development and testing environments for data engineers
- **Code Location GitOps:** Production-grade data pipelines with full GitOps automation

### 7.2 Deployment Templates

#### Platform GitOps Template
Manages the core Dagster infrastructure components:
- Dagster daemon and webserver deployment
- PostgreSQL metadata database
- Shared compute resources and configuration
- Cross-namespace RBAC and service mesh integration

#### Code Location Source Template
Provides isolated development environments:
- Individual namespace per data engineering team
- Direct Git repository integration for rapid iteration
- Sandbox compute resources with development-friendly policies
- Integration with existing CI/CD workflows for testing

#### Code Location GitOps Template
Production-ready pipeline deployment:
- Full GitOps automation with Argo CD integration
- Separate namespaces for staging and production
- Resource quotas and security policies enforcement
- Automated promotion workflows aligned with application deployment patterns

### 7.3 Database Architecture
**PostgreSQL** is selected as the primary database for Dagster metadata storage:
- Centralized metadata repository for all pipeline definitions and execution history
- Integration with existing PostgreSQL operator from luban-bootstrapper
- Automated backup and disaster recovery through established patterns
- Connection pooling and performance optimization for high-throughput scenarios

### 7.4 Exposure Strategy
Dagster services are exposed through **Envoy Gateway** following established patterns:
- Web UI accessible via authenticated routes with SSO integration
- gRPC endpoints for programmatic access with mTLS authentication
- Separate ingress configurations for development, staging, and production environments
- Integration with existing monitoring and logging infrastructure

### 7.5 Integration with Existing CI/CD
Dagster pipelines participate in the established GitOps workflow:
- Pipeline definitions stored in Git repositories alongside application code
- Automated testing and validation through Argo Workflows
- Promotion from sandbox to production following the same approval patterns
- Resource provisioning and namespace management through luban-provisioner
