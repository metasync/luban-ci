# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.5.0] - 2026-01-28

### Changed
- **Buildpack**: Updated `python-uv` buildpack to `0.0.8`.
- **Buildpack**: Removed `Procfile` parsing logic. The buildpack no longer sets a default start command.
- **Buildpack**: Optimized `bin/build` script to rely on standard CNB `launch=true` mechanism for `PATH` configuration, removing redundant `PATH` manipulation.
- **Deployment**: Applications using this buildpack should now specify their start command using `args` in Kubernetes manifests (e.g., `args: ["uv", "run", ...]`) to ensure the CNB launcher is correctly invoked.

### Fixed
- **Buildpack**: Fixed issue where `uv` might not be in `PATH` during launch by ensuring correct layer metadata.
- **Builder**: Resolved `manifest unknown` error for run image during Kpack builder creation by ensuring `luban-kpack-builder:al2023-run-image` is published.

## [v0.4.0] - 2026-01-26

### Changed
- **Gateway**: Transitioned to a Shared Gateway architecture. Webhooks now use `luban-gateway` via the `luban-ci` wildcard listener instead of a dedicated `webhook-gateway`.
- **Testing**: Replaced shell-based `webhook-test` with a robust Python script (`test/webhook_test.py`) for better reliability and correct signature generation.
- **Sample App**: Moved `sample-app` to a separate repository `luban-hello-world-py`.
- **Workflow**: Updated CI workflows to point to the new `luban-hello-world-py` repository.
- **Workflow**: Removed `sub_path` usage in default workflows as the app is now at the repository root.

### Fixed
- **Gateway**: Resolved port conflicts by consolidating webhook ingress traffic through the shared `luban-gateway`.
- **Webhook**: Fixed HMAC signature validation failures by ensuring correct payload formatting and adding required headers.
- **Testing**: Fixed `make test` failure by updating kpack workflow to tag images with git revision (matching `make test` expectation).
- **Testing**: Fixed `make test` target to use correct application name and revision.

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
