# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- **Workflow Refactoring**:
  - Split `ci-workflow.yaml` into reusable `ci-dind-workflow-template.yaml` and lightweight `ci-dind-workflow.yaml`.
  - Renamed workflow generation name to `luban-ci-dind-`.
  - Parameterized `stack_tag` and `quay_namespace` for better reusability.
- **Makefile**:
  - Updated `pipeline-deploy` to apply the new WorkflowTemplate.
  - Updated `pipeline-run` to use the new Workflow instance.
- **Documentation**:
  - Updated `README.md`, `PLAN.md`, and `REQUIREMENTS.md` to reflect the current architectural state.

### Added
- **Python-UV Buildpack**:
  - Added support for `.uv-version` file to specify custom `uv` version.
- **Argo Workflow Integration**: End-to-end CI pipeline manifest (`ci-workflow.yaml`) supporting Clone, Build, and Push steps.
- **Custom CNB Stack**:
  - Amazon Linux 2023 Minimal base images.
  - Non-root user (UID 1000) execution.
  - Custom Build and Run images (`luban-ci/build`, `luban-ci/run`).
- **Python-UV Buildpack**:
  - Custom buildpack using `uv` for fast Python dependency management.
  - Persistent cache for `uv` virtual environments.
  - Dynamic `detect` logic based on `.python-version`.
- **Infrastructure**:
  - `Makefile` for project management (secrets, build, deploy).
  - Kubernetes RBAC (`pipeline-sa.yaml`) for secure workflow execution.
- **Sample App**: FastAPI application for pipeline verification.

### Fixed
- **Permissions**: Resolved ServiceAccount RBAC issues for Argo Workflow output artifacts.
- **Buildpack**: Fixed `uv` download and caching mechanisms.
- **Quay.io Auth**: Handled Robot Account namespace parsing in push scripts.
- **Environment**: Switched to `ubuntu` base for pipeline steps to ensure tool availability (`curl`, `tar`, `bash`).
