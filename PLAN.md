# Luban CI Agile Development Plan

This plan breaks down the implementation of `luban-ci` into iterative, testable milestones. Each phase delivers a functional component of the system.

## Phase 1: Foundation - The Custom Stack
**Goal:** Create and verify the base Amazon Linux stack (Build & Run images) that enforces non-root execution.
**Deliverables:**
1.  `stack/build/Dockerfile`: Amazon Linux-based build image with necessary build tools.
2.  `stack/run/Dockerfile`: Minimal Amazon Linux-based run image with non-root user configuration.
3.  `stack.toml`: Configuration for the stack.
4.  **Verification:** Build the stack images using `pack` and verify the non-root user exists in the run image.

## Phase 2: The Python + uv Buildpack
**Goal:** Implement the logic to detect Python apps, install Python via `uv`, and manage dependencies.
**Deliverables:**
1.  `buildpacks/python-uv/bin/detect`: Script to check for `uv.lock` or `.python-version`.
2.  `buildpacks/python-uv/bin/build`: Script to install `uv`, resolve Python version, and install dependencies.
3.  `buildpacks/python-uv/buildpack.toml`: Buildpack metadata.
4.  **Verification:** Manually run `pack build` on a sample Python app using this buildpack and the Phase 1 stack locally.

## Phase 3: Trusted Builder
**Goal:** Combine the Stack and Buildpack into a distributable "Trusted Builder" image.
**Deliverables:**
1.  `builder.toml`: Configuration linking the stack and the python-uv buildpack.
2.  **Verification:** Create the builder image and use it to build the sample Python app. Ensure the resulting image runs successfully.

## Phase 4: CI Pipeline - Build (Argo Workflows)
**Goal:** Automate the build process using Argo Workflows.
**Deliverables:**
1.  `workflows/build-template.yaml`: Argo WorkflowTemplate that runs `pack build` using the Trusted Builder.
2.  **Verification:** Manually submit a workflow that clones a repo, builds the image, and pushes it to Quay.io.

## Phase 5: CI Pipeline - Trigger (Argo Events)
**Goal:** Connect GitHub events to the Build Workflow.
**Deliverables:**
1.  `events/event-source.yaml`: Configuration for GitHub Webhooks.
2.  `events/sensor.yaml`: Sensor to trigger the Build Workflow on push events.
3.  **Verification:** Push a commit to a test repo and verify the workflow starts automatically.

## Phase 6: CD Pipeline - Deploy (Argo CD)
**Goal:** Close the loop by updating the deployment when a new image is built.
**Deliverables:**
1.  `argocd/application.yaml`: Argo CD Application manifest for the test app.
2.  **Integration:** Update Phase 4 workflow to trigger a Git commit (updating the image tag in the infra repo) or directly trigger Argo CD sync.
3.  **Verification:** End-to-end test: Code Push -> Build -> Push Image -> Deploy -> App Updated.
