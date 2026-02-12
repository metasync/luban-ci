# Luban CI Agile Development Plan

This plan breaks down the implementation of `luban-ci` into iterative, testable milestones. Each phase delivers a functional component of the system.

## Phase 1: Foundation - The Custom Stack [Completed]
**Goal:** Create and verify the base Amazon Linux stack (Build & Run images) that enforces non-root execution.
**Deliverables:**
1.  `stack/build/Dockerfile`: Amazon Linux-based build image with necessary build tools.
2.  `stack/run/Dockerfile`: Minimal Amazon Linux-based run image with non-root user configuration.
3.  `stack.toml`: Configuration for the stack.
4.  **Verification:** Build the stack images using `pack` and verify the non-root user exists in the run image.

## Phase 2: The Python + uv Buildpack [Completed]
**Goal:** Implement the logic to detect Python apps, install Python via `uv`, and manage dependencies.
**Deliverables:**
1.  `buildpacks/python-uv/bin/detect`: Script to check for `uv.lock` or `.python-version`.
2.  `buildpacks/python-uv/bin/build`: Script to install `uv`, resolve Python version, and install dependencies.
3.  `buildpacks/python-uv/buildpack.toml`: Buildpack metadata.
4.  **Verification:** Manually run `pack build` on a sample Python app using this buildpack and the Phase 1 stack locally.

## Phase 3: Trusted Builder [Completed]
**Goal:** Combine the Stack and Buildpack into a distributable "Trusted Builder" image.
**Deliverables:**
1.  `builder.toml`: Configuration linking the stack and the python-uv buildpack.
2.  **Verification:** Create the builder image and use it to build the sample Python app. Ensure the resulting image runs successfully.

## Phase 4: CI Pipeline - Build (Legacy DinD) [Removed]
This phase used Docker-in-Docker with Argo Workflows and has been retired in favor of kpack. The system now uses kpack exclusively for builds.

## Phase 4b: CI Pipeline - kpack Integration [Completed]
**Goal:** Migrate to Kubernetes-native builds using kpack.
**Deliverables:**
1.  `manifests/kpack-stack.yaml` & `manifests/kpack-builder.yaml`: kpack resource definitions.
2.  `manifests/ci-kpack-workflow-template.yaml`: Workflow using `kp` CLI to trigger builds.
3.  **Verification:** Trigger kpack builds via Argo Workflows and verify image creation.

## Phase 5: CI Pipeline - Trigger (Argo Events) [Completed]
**Goal:** Connect GitHub events to the Build Workflow.
**Deliverables:**
1.  `events/event-source.yaml`: Configuration for GitHub Webhooks.
2.  `events/sensor.yaml`: Sensor to trigger the Build Workflow on push events.
3.  **Verification:** Push a commit to a test repo and verify the workflow starts automatically.

## Phase 6: CD Pipeline - Deploy (Argo CD) [Completed]
**Goal:** Close the loop by updating the deployment when a new image is built.
**Deliverables:**
1.  `argocd/application.yaml`: Argo CD Application manifest for the test app.
2.  **Integration:** Update Phase 4 workflow to trigger a Git commit (updating the image tag in the infra repo) or directly trigger Argo CD sync.
3.  **Verification:** End-to-end test: Code Push -> Build -> Push Image -> Deploy -> App Updated.

## Phase 7: Developer Experience & Robustness [Completed]
**Goal:** Refactor the pipeline for stability, usability, and easier onboarding.
**Deliverables:**
1.  **Argo Template Refactoring**: Moved logic from complex Argo expressions to native shell scripts within containers for better reliability.
2.  **Luban App Setup Enum**: Added `setup_source_repo` enum parameter to allow developers to opt-out of source repo provisioning (e.g., when migrating existing apps).
3.  **Automatic Org Fallback**: Improved organization detection logic to automatically use the project name if no organization is specified.
4.  **Makefile Enhancements**: Standardized deployment and testing targets.

## Phase 8: Unified Provisioner & Azure DevOps Support [Completed]
**Goal:** Consolidate provisioning tools into a single, robust Python application (`luban-provisioner`) and add support for Azure DevOps.
**Deliverables:**
1.  **Unified Tool**: `tools/luban-provisioner` now handles GitOps repo, source repo, and project namespace provisioning.
2.  **Provider Abstraction**: Implemented `provider_factory.py` to support pluggable Git providers.
3.  **GitHub & Azure Support**:
    - **GitHub**: Native API integration for repos, webhooks, and branch protection.
    - **Azure DevOps**: Support for Project/Repo creation, Pull Requests, and Webhooks.
4.  **Simplified Workflows**: Updated all workflows to rely on the unified tool and new parameters (`git_provider`, `git_server`).

## Phase 9: Refactoring & Standardization [Completed]
**Goal:** Enhance code maintainability, security, and developer experience.
**Deliverables:**
1.  **Tooling Refactoring**:
    - Refactored `luban-provisioner` to use a consistent `provider_factory` pattern.
    - Optimized Dockerfiles for `gitops-utils` and `luban-provisioner` (non-root users, version pinning).
    - Removed unnecessary dependencies (e.g., `crane` from `gitops-utils`).
2.  **Test Suite Enhancements**:
    - Standardized test configuration in `test/Makefile.env`.
    - Added `patch-coredns` tool for local DNS resolution during testing.
    - Improved `webhook_test` scripts to support dynamic project names.
3.  **Documentation Updates**:
    - Comprehensive README updates for `luban-provisioner` and root project.
    - Documented local testing workflows and DNS patching.
