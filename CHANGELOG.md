# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.6.7] - 2026-02-03

### Added
- **Developer Experience**: Added `setup_source_repo` parameter with `yes`/`no` enum to `luban-app-setup-template`, allowing optional source repo provisioning.
- **Developer Experience**: Added `luban-promotion-template` to facilitate environment promotion from `snd` to `prd` via Pull Requests in the GitOps repository.
- **Infrastructure**: Integrated `source-repo-workflow-template.yaml` and `promotion-workflow-template.yaml` into the automated deployment pipeline (Makefile).

### Changed
- **Robustness**: Refactored all workflow templates to use native shell logic instead of complex Argo expressions for parameter derivation (e.g., Git organization fallback, URL construction).
- **Documentation**: Updated `README.md` and `PLAN.md` to reflect new architecture and features.

### Fixed
- **Stability**: Standardized enum values to lowercase and fixed case-sensitive `when` conditions in workflows.
- **Build**: Resolved `kp` image tagging issues by using explicit shell logic in `luban-ci-kpack-workflow-template`, preventing positional argument errors.

## [v0.6.6] - 2026-02-02

### Added
- **Buildpack**: Updated `python-uv` to `v0.0.9`, introducing support for `pyproject.toml` entrypoint detection.
  - Automatically parses `[project.scripts]` to generate a `launch.toml` with `uv run <script_name>` as the default process.
  - Supports common script names: `app` or `start`.
- **Testing**: Added comprehensive `make` targets for testing the CI pipeline and webhooks:
  - `test-ci-pipeline`: Triggers the CI workflow via Argo CLI with customizable parameters.
  - `test-events-webhook`: Simulates a GitHub push event using a shell script (dependency-free).
  - `test-events-webhook-py`: Simulates a GitHub push event using Python.
- **Documentation**: Added a dedicated "Development & Testing" section to `README.md`.

### Changed
- **Makefile**: Refactored test targets (`test-ci-pipeline-run` -> `test-ci-pipeline`) and exposed them in the root Makefile for easier access.
- **Testing**: Updated webhook test scripts to support environment variable overrides (`APP_NAME`, `REPO_URL`, etc.).
- **Buildpack**: Reverted `Procfile` support in favor of `pyproject.toml` or explicit Kubernetes `args`.

## [v0.6.5] - 2026-02-02

### Architecture
- **ConfigMap Driven**: Transitioned to using `luban-config` ConfigMap as the single source of truth for platform configuration (ports, domains, registry, secrets).
- **Consistency**: Refactored all workflow templates (`luban-project`, `luban-app`, `argocd-project`, `harbor-project`) to consume values from `luban-config`.

### Changed
- **Workflow**: Updated `luban-ci-kpack-workflow-template` to robustly handle "Day 1" GitOps updates by performing a one-time global replacement of the placeholder image name in all manifests.
- **Provisioner**: Updated `gitops-provisioner` to `v0.1.7`, adding support for split `default_image_name` and `default_image_tag` parameters.
- **Template**: Updated Cookiecutter template to use parameterized default image instead of hardcoded `quay.io` value.
- **Fix**: Resolved issue where GitOps repo update failed to replace the default image name in `base/deployment.yaml` and `overlays/kustomization.yaml`.

## [v0.6.4] - 2026-01-31

### Changed
- **Infrastructure**: Migrated Harbor and CI workflows to use the public domain `harbor.orb.metasync.cc` with a valid Let's Encrypt wildcard certificate (managed via Cloudflare DNS-01).
- **Cleanup**: Removed local TLS configuration tools (`tools/configure-kpack-tls.sh`) as they are no longer needed with valid certificates.
- **DNS**: Updated `tools/patch-coredns.sh` to resolve the new public domain to the local LoadBalancer IP.

## [v0.6.3] - 2026-01-31

### Added
- **DevEx**: Added `make configure-kpack` and `tools/configure-kpack-tls.sh` to automate Kpack TLS trust configuration for local Harbor in OrbStack environments.

## [v0.6.2] - 2026-01-31

### Changed
- **Consistency**: Updated `harbor-project-workflow-template` and `luban-project-workflow-template` to default to the external Harbor URL `https://harbor.k8s.orb.local`, aligning with the CI pipeline and production architecture.

## [v0.6.1] - 2026-01-31

### Fixed
- **Infrastructure**: Addressed DNS resolution issues for `harbor.k8s.orb.local` in OrbStack environments by updating CoreDNS configuration.
- **Security**: Explicitly attached `harbor-creds` to the `luban-ci-sa` ServiceAccount, enabling kpack to authenticate with the internal Harbor registry.

## [v0.6.0] - 2026-01-31

### Changed
- **Workflow**: Fixed "User cannot get resource secrets" error in `gitops-repo-workflow-template` by explicitly defining the container `command`, bypassing Argo's image entrypoint lookup.
- **Workflow**: Removed unused `default_image` parameter from `gitops-repo-workflow-template` and `luban-app-workflow-template` interfaces.
- **Workflow**: Enhanced `push-to-github` script to handle repository existence gracefully (idempotency) and added fallback support for User vs Organization endpoints.
- **Workflow**: Enforced naming convention: GitOps repositories are now strictly named `<app-name>-gitops`.
- **Provisioner**: Updated `gitops-provisioner` to `v0.1.5`, removing the deprecated `--default-image` argument from `entrypoint.py`.
- **Documentation**: Comprehensive update to `README.md`, documenting the Project vs App setup workflows, naming conventions, and environment mappings.

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
