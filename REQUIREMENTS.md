# Luban CI Requirements

## 1. Project Overview
**Project Name:** `luban-ci`
**Goal:** Build a flexible, extensible, GitOps-based Continuous Integration (CI) system.
**Platform:** Kubernetes (OrbStack for local development).
**Scope:** The underlying CI/CD platform infrastructure is assumed to be pre-provisioned by [luban-bootstrapper](https://github.com/metasync/luban-bootstrapper). `luban-ci` focuses on the *pipeline implementation* and *custom buildpack ecosystem*.

**Design Principles:**
*   **Extensibility:** While Python is the initial supported language, the architecture must support adding other languages (e.g., Go, Java, Node.js) in the future without major refactoring.
*   **Security:** Security defaults are mandatory. This includes non-root execution, minimal base images, and standard compliance.

## 2. Infrastructure & Technology Stack
The following components are assumed available via `luban-bootstrapper`:
- **Orchestration:** Argo Workflows
- **Event Bus:** Argo Events
- **Continuous Delivery:** Argo CD
- **Build Engine:** Cloud Native Buildpacks (CNB) via `pack` CLI
- **Ingress/Gateway:** Envoy Gateway (as per bootstrapper spec)
- **Container Registry:** Quay.io (External)

## 3. Pipeline Architecture
The CI/CD process must follow a strict GitOps workflow and use modular templates to support multiple languages.

### 3.1. Trigger Phase (Argo Events)
- **Source:** GitHub Webhooks (push/PR events).
- **Mechanism:** Argo Events receives the webhook and triggers an Argo Workflow sensor.
- **Payload:** Passes Git metadata (commit SHA, branch, repo URL) to the workflow.

### 3.2. Build Phase (Argo Workflows)
A workflow template must be designed to execute the following steps:
1.  **Checkout:** Clone the source code repository.
2.  **Language Detection / Configuration:** Determine the build strategy based on repository content or configuration.
3.  **Build & Publish:**
    -   Use `pack` CLI to build the OCI container image.
    -   Push the image to Quay.io.
    -   **Constraint:** Must use the custom Buildpack ecosystem defined in Section 4.

### 3.3. Deploy Phase (Argo CD)
-   Upon successful build/push, trigger a deployment update.
-   Argo CD syncs the new image version to the target Kubernetes cluster.

## 4. Custom Buildpacks Ecosystem (General)
To support modern development standards and security requirements, we will develop a custom Cloud Native Buildpacks stack.

### 4.1. Security & Compliance
-   **Non-Root Execution:** All applications running inside the built container images **must** run as a non-root user. The stack's Run Image must define and enforce this user.
-   **Minimal Base Image:** Both Build and Run images must use a minimal distribution (Amazon Linux Minimal) to reduce the attack surface.
-   **SBOM:** Ensure Software Bill of Materials generation is preserved (standard feature of CNB).

### 4.2. Stack Components
We need to define and build the following CNB artifacts:
1.  **Build Image:** Contains build-time dependencies (compilers, headers) based on Amazon Linux.
2.  **Run Image:** Minimal runtime environment based on Amazon Linux, configured with a non-root user.
3.  **Trusted Builder:** A composite builder image referencing the stack and buildpacks.

## 5. Language Support: Python (Initial Implementation)
Specific requirements for the Python language support.

### 5.1. Python Buildpack Requirements
-   **Dependency Manager:** `uv` (no pip/poetry legacy flows unless wrapped by uv).
-   **Python Version Management:**
    -   Must respect `.python-version` file in the source repository.
    -   `uv` must handle the installation of the requested Python version.
-   **Compliance:** All images and lifecycle steps must adhere to the official [Buildpacks Platform API](https://github.com/buildpacks/spec).

## 6. Deliverables
1.  **CNB Stack Definitions:** Dockerfiles for Amazon Linux-based Build and Run images (enforcing non-root).
2.  **Custom Buildpack:** Implementation for Python + uv logic.
3.  **Builder Config:** `builder.toml` configuration.
4.  **Argo Resources:**
    -   `EventSource` and `Sensor` manifests for GitHub.
    -   `WorkflowTemplate` for the CI pipeline (parameterized for future languages).
    -   `Application` manifests for Argo CD.
