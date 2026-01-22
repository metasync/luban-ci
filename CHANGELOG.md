# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Sample App**: Moved `sample-app` to a separate repository `luban-hello-world-py`.
- **Workflow**: Updated CI workflows to point to the new `luban-hello-world-py` repository.
- **Workflow**: Removed `sub_path` usage in default workflows as the app is now at the repository root.

## [v0.3.0] - 2026-01-22

### Added
- **kpack Integration**: Migrated build pipeline to use kpack (Kubernetes Native Buildpacks).
- **kpack Workflow**: Added `ci-kpack-workflow-template.yaml` and related manifests (`kpack-stack.yaml`, `kpack-builder.yaml`).
- **kp CLI**: Integrated `kp` CLI for image resource management in Argo Workflows.
- **Makefile**: Added `pipeline-run-kpack` target (default) and `pipeline-logs`.

### Changed
- **Documentation**: Updated `README.md` to reflect kpack usage and removal of manual kpack installation (managed externally).
- **Workflow**: `sub_path` is now an optional parameter in the workflow template.
- **Refactor**: Removed `kpack-install` from Makefile as it is managed by `luban-bootstrapper`.

## [v0.2.0] - 2026-01-21

### Added
- **Python uv Support**: Added support for `.uv-version` configuration file to specify custom uv versions.
- **Testing**: Enhanced `make test` with retry loops and better error handling.

### Changed
- **Workflow**: Refactored `ci-workflow.yaml` into reusable `WorkflowTemplate` and `Workflow` manifests.
- **Docs**: Updated documentation to include new testing procedures and configuration options.

### Fixed
- **Testing**: Fixed `make test` target to use correct application name and revision.
- **Testing**: Addressed issues with Docker container cleanup during tests.

## [v0.1.0] - 2026-01-21

### Added
- **Initial Release**: Basic CI pipeline structure.
- **Stack**: Custom Amazon Linux 2023 Minimal based stack (Build & Run images).
- **Buildpack**: Custom Python buildpack using `uv`.
- **Secrets**: Secret management for GitHub and Quay.io credentials.
- **Robot Accounts**: Added support for Quay.io robot accounts in secret handling.

### Changed
- **Configuration**: Revised default namespace for image registry.
