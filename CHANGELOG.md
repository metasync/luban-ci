# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

## [v1.0.8] - 2026-03-31

### Changed

- **Workflows**: Updated `synchronization.semaphore` to `synchronization.semaphores` for Argo Workflows v4 compatibility.

### Docs

- Added a Secrets roadmap section to track the per-env secrets namespace and ESO/Vault direction.

## [v1.0.7] - 2026-03-29

### Changed

- Aligns this release with `luban-provisioner-v0.3.7` and associated workflow/config/documentation updates.

## [luban-provisioner-v0.3.7] - 2026-03-29

### Changed

- **Git HTTPS**: Switched to provider-scoped config (`<provider>_https_auth_mode`, `<provider>_base_url`, `<provider>_basic_auth_username`) and wired workflows to pass `GIT_HTTPS_AUTH_MODE`/`GIT_BASE_URL`/`GIT_BASIC_AUTH_USERNAME`.
- **Git HTTPS**: Added header-based auth mode (`extraheader_basic`) to support Azure DevOps Server (on-prem) without persisting PATs in `~/.git-credentials`.

## [v1.0.6] - 2026-03-28

### Changed

- Aligns this release with `luban-provisioner-v0.3.5` and associated workflow/config/documentation updates.

## [luban-provisioner-v0.3.5] - 2026-03-28

### Added

- **Git HTTPS (Azure DevOps Server)**: Added header-based auth mode (`extraheader_basic`) to avoid persisting PATs in `~/.git-credentials`.
- **Git HTTPS (Azure DevOps Server)**: Added `azure_base_url` support for deployments with path prefixes (e.g. `/tfs`).

### Changed

- **Git HTTPS**: `git` subprocess calls now honor header-based auth when enabled.

## [v1.0.5] - 2026-03-28

### Changed

- Aligns this release with `luban-provisioner-v0.3.4` and associated workflow/config/documentation updates.

## [luban-provisioner-v0.3.4] - 2026-03-28

### Changed

- **Provisioner**: Bumped `luban-provisioner` to `0.3.4`.
- **Dagster GitOps**: Enhanced `dagster-code-location` GitOps template to include app-scoped `<app_name>-config` ConfigMap and `<app_name>-secret` Secret (with replicator stubs in overlays).
- **Dagster GitOps**: Made dbt/StarRocks env vars conditional on `template_type` and standardized StarRocks DB naming to use `package_name`.

## [v1.0.4] - 2026-03-27

### Changed

- Aligns this release with `luban-provisioner-v0.3.2` and associated workflow/config/documentation updates.

## [luban-provisioner-v0.3.2] - 2026-03-27

### Changed

- Standardized git HTTPS auth to use git's credential mechanism (no PATs embedded in remote URLs).
- Added `GIT_USERNAME`/`--git-username` support across provisioner commands and workflow templates.
- Normalized `git_server` handling and redacted clone URL logs to reduce accidental secret exposure.

## [v1.0.3] - 2026-03-26

### Changed

- Aligns this release with `luban-provisioner-v0.3.0` and associated workflow/config updates.

## [luban-provisioner-v0.3.0] - 2026-03-26

### Added

- **Provisioner**: Added `luban-dagster-dbt-starrocks-code-location` source template for data transformation teams using dbt + StarRocks + Dagster.
- **Provisioner**: Added corresponding GitOps and workflow templates (`luban-dagster-dbt-starrocks-code-location-setup-template`).
- **Buildpack**: Added `dbt manifest.json` pre-generation during the build phase for Dagster + dbt code locations. The buildpack now runs `dbt deps` (if packages detected) and `dbt parse` to produce a pre-baked manifest, eliminating `DagsterDbtManifestNotFoundError` at startup.
- **Docs**: Added `docs/dagster/concepts/dagster-dbt-code-location-template.md` documenting the dbt/Dagster boundary, runtime contract, and conventions.

### Changed

- **Buildpack**: Bumped `python-uv` buildpack to `v0.0.38`.
- **Provisioner**: Bumped `luban-provisioner` to `0.3.0`.
- **Docs**: Removed remaining `LUBAN_DBT_PREPARE_IF_DEV` mention in `template_usage.md`.
- **Template**: Added `docker/docker-compose.yml` and Makefile targets to spin up local StarRocks.
- **Template**: Fixed local startup by auto-preparing dbt manifest when missing (`LUBAN_DBT_PREPARE_ON_LOAD`).
- **Provisioner**: Added optional ODS test models to generate `ods.customers` and `ods.orders` on demand.
- **Template**: Added `make ods-test-bootstrap` and `make ods-test-append` for bootstrap + incremental arrival simulation.
- **Template**: Switched ODS test generation to StarRocks `generate_series()` for 10k+ row scalability.
- **Template**: Standardized StarRocks DB env vars as full database names and documented the convention.
- **Template**: Removed unsupported dbt StarRocks incremental `merge` strategy from DWD/DWS models.
- **Template**: Fixed StarRocks ODS database resolution by removing cookiecutter raw blocks from dbt source/schema configs.
- **Template**: Centralized StarRocks DB env var usage into dbt macros for SQL resources.
- **Template**: Compute StarRocks DWD/DWS schema by node folder in `generate_schema_name` to avoid unevaluated Jinja in `dbt_project.yml`.
- **Template**: Refactored StarRocks layer schema selection into a helper macro for readability.
- **Template**: Avoided `dynamic_overwrite` partitioning in `orders` to prevent empty-partition inserts.
- **Template**: Added StarRocks `use_pure` option and `DBT_THREADS` env override to avoid dbt runtime segfaults.
- **Docs**: Updated StarRocks template docs to reflect current dbt configs and tuning env vars.
- **Template**: Generates `manifest.json` on load when missing via `assets/lib/dbt_prepare.py` (controlled by `LUBAN_DBT_PREPARE_ON_LOAD`).
- **Template**: Defaulted `default_env` to `development` for local-first workflows.
- **Template**: Added `dbt-parse` target and made dbt targets run `dbt deps` automatically.
- **Template**: Renamed `finalize_orders_daily_schedule` to `orders_daily_schedule` and set schedules default to running.
- **Template**: Default ODS observation DB to `${STARROCKS_DB}_ods` when `STARROCKS_ODS_DB` is unset.
- **Provisioner**: Updated GitOps template routing to use explicit `elif` chain for `dagster-platform` / `dagster-code-location` variants, replacing legacy fallback heuristics.
- **Provisioner**: Updated `profiles.yml` to use `{{cookiecutter.package_name}}` instead of `{{cookiecutter.app_name}}` for dbt project name and profile, ensuring Python-identifier-safe names.
- **Provisioner**: Updated `profiles.yml` to use `env_var('STARROCKS_*', '<default>')` defaults, making the buildpack adapter-agnostic — no `STARROCKS_*` env vars need to be set during build.
- **Provisioner**: Refined the Dagster+dbt+StarRocks code location source template to standardize on orchestration-level lookback and simplify schedule/job configuration.
- **Docs**: Updated the Dagster+dbt+StarRocks template usage docs to remove hourly partition references.
- **Template**: Removed hourly partition configuration from `.env.example` to match the shipped daily-only partition setup.
- **Template**: Removed hourly partition support for now due to Dagster auto-materialize subset limitations with mixed partition definitions.
- **Azure DevOps**: Standardized Azure DevOps REST API version selection as configuration via `luban-config.azure_devops_api_version` (exported to workflows as `AZURE_DEVOPS_API_VERSION`), removing runtime API-version probing.
- **Workflows**: Improved `luban-ci-kpack-workflow-template` to wait for the correct `BUILD_REV` match before proceeding, fixing a race condition on fast-rebuilding images.

### Fixed

- **Buildpack**: Added `|| exit 1` error handling on both `uv run dbt deps` and `uv run dbt parse` calls, and added manifest file existence verification after `dbt parse`.
- **Buildpack**: Added error handling on `wget` downloads for uv and its SHA256 checksum.
- **Provisioner**: Improved error message in `gitops.py` `except Exception` handler to include the output directory path.
- **Provisioner**: Fixed `row_count_greater_than` generic test definitions in `dwd/schema.yml` and `dws/schema.yml` to use dbt v1.11 `arguments:` nesting (was deprecated at top level).
- **Provisioner**: Fixed `relationships` generic test in `sources.yml` to use dbt v1.11 `arguments:` nesting.
- **Docs**: Removed stale `source_template_type` parameter reference from `docs/dagster/concepts/dagster-integration.md`.
- **Config**: Removed duplicate commented `webhook_url` entry in `luban-config.yaml`.
- **Template**: Fixed `dbt_cli_build_job` execution failing with `KeyError: 'nodes'` by switching CLI jobs to stream raw dbt events and wait for completion (no manifest-based asset event mapping).

### Docs

- Documented dbt/Dagster boundary, repository layout, runtime contract, local development workflow, layer conventions, and extension patterns in `docs/dagster/concepts/dagster-dbt-code-location-template.md`.

## [v1.0.1] - 2026-03-16

### Added
- **Buildpack**: Added optional air-gapped mirror support for `uv` and managed Python downloads.
- **kpack**: Added `ClusterLifecycle` manifest and pinned lifecycle image by digest for reproducible builds.

### Changed
- **Buildpack**: Bumped `python-uv` buildpack to `v0.0.33`.
- **kpack**: Standardized builder image naming to `luban-kpack-builder` and updated `ClusterBuilder`/config references.
- **CI Workflow**: Injected mirror configuration into kpack `Image.spec.build.env` from `luban-config`.

### Fixed
- **GitOps Update**: Fixed branch checkout to use `git checkout <branch>` instead of path checkout.
- **Dispatcher**: Fixed Azure DevOps URL parsing for legacy `DefaultCollection` URL shapes.

### Docs
- Documented air-gapped mirror URL layouts, lifecycle pinning rationale, CoreDNS patching for local clusters, and GitOps branch behavior.

## [v1.0.0] - 2026-03-15

### Architecture
- **Multi-Cluster v2**: Formalized the split between an **admin/control-plane cluster** (CI + ArgoCD + registry access) and **worker/runtime clusters** (application workloads).
  - Introduced a centralized infra-repo pattern: `luban-infra-ci` (CI infra) and `luban-infra-cd` (CD/ArgoCD infra), with per-app GitOps repos kept application-only.
  - Added environment → cluster routing via `luban-config.cluster_map` and updated ArgoCD provisioning templates to resolve `spec.destination.server` from it.

### Added
- **Provisioner**: Added `luban-provisioner infra` commands to init/update centralized infra repos (CI and CD overlays).
- **Workflows**: Added infra provisioning/update workflow templates to support the centralized infra-repo + multi-cluster approach.
- **Docs**: Added/expanded multi-cluster architecture documentation and aligned guides with the centralized infra-repo pattern.

### Changed
- **CI Project Defaults**: Default Harbor project visibility is now `private` in `luban-project-setup-template`.
- **Provisioner**: Updated `luban-provisioner` image to `0.2.0`.

### Docs
- Moved planning and requirements documents under `docs/` and refreshed guides to match current secrets and workflow behavior.

### Fixed
- **Secrets**: Standardized secrets application via `manifests/secrets/templates/*` and `manifests/secrets/setup-secrets.sh`, including correct handling of `$` in `secrets/*.env`.

### Removed
- **Legacy Templates**: Removed the deprecated per-project `templates/project/*` scaffolding in favor of the centralized infra-repo templates.

### Fixed
- **kpack Workflow**: Improved `luban-ci-kpack` reliability by targeting the correct `ci-<project>` namespace, handling kpack `latestBuildRef` shape differences, waiting on the `Build` `Succeeded` condition, and starting log streaming as soon as a Build is created.
- **Secret Replication**: Standardized `azure-ssh-creds` in `ci-*` namespaces as a placeholder `kubernetes.io/ssh-auth` Secret replicated from `luban-ci`, while ensuring GitOps does not overwrite replicated key material.
- **RBAC**: Granted `luban-ci-sa` the minimal kpack permissions required to manage `Image` resources and observe `Build` status.

## [v0.9.6] - 2026-03-04

### Architecture
- **Identity & Access**: Refactored Project Provisioning to use ServiceAccount-based RBAC instead of direct Group bindings, enabling seamless integration with Argo Workflows SSO.
  - Introduced `project-admin` and `project-developer` ServiceAccounts in project namespaces.
  - Configured `workflows.argoproj.io/rbac-rule` annotations to map OIDC groups to these ServiceAccounts.
  - Enabled `SSO_DELEGATE_RBAC_TO_NAMESPACE=true` in Argo Workflows to support multi-tenant RBAC.
  - Explicitly managed ServiceAccount tokens (Secrets) for Argo Workflows integration on K8s 1.24+.
- **Tunnel**: Updated Cloudflare Tunnel configuration to use short internal service names, resolving upstream connection issues (530 errors).

### Changed
- **Templates**: Updated `luban-project-workflow-template` and `luban-provisioner` to accept single OIDC group names (`admin_group`, `developer_group`) instead of lists, simplifying configuration.
- **Templates**: Added `imagePullSecrets` to Dagster Platform ServiceAccounts, ensuring private registry images can be pulled by Daemon/Webserver pods.
- **Infrastructure**: Updated `cloudflared` image to `2026.2.0` and relaxed Liveness Probes to improve tunnel stability.

### Fixed
- **Provisioner**: Fixed `jinja2.exceptions.UndefinedError` in `view-templates-binding.yaml` by updating legacy variable references.
- **Tunnel**: Resolved `530 Origin DNS Error` for Azure DevOps webhooks by correcting the internal service DNS resolution.

## [v0.9.5] - 2026-02-25

### Added
- **Configuration**: Added support for custom Python Package Index (`python_index_url`) in `luban-config`.
- **Templates**: Updated Dagster and Python source templates to support custom PyPI mirrors/indexes in `pyproject.toml`.
- **Tooling**: Updated `luban-provisioner` (v0.1.226) to support index configuration injection.

### Changed
- **Buildpack**: Updated `python-uv` buildpack (v0.0.32) to skip development dependencies (`--no-dev`) during production builds, optimizing image size.

## [v0.9.4] - 2026-02-25

### Architecture
- **Tooling**: Standardized all provisioning logic into `luban-provisioner` (v0.1.223), improving security and maintainability.
- **Workflow**: Updated all workflow templates to explicitly pass Git credentials and server configuration, removing reliance on fragile implicit environment variables.
- **Configuration**: Unified `luban-config` key naming for Git providers (`github_server`, `azure_server`) to support cleaner dynamic lookups in workflows.

### Changed
- **Workflow**: Refactored `luban-promotion-workflow-template` and other core templates to use a consistent, explicit argument passing pattern for `git-token` and `git-server`.
- **Workflow**: Removed `optional: true` from critical credential environment variables to ensure fail-fast behavior when configuration is missing.
- **Workflow**: Normalized indentation and YAML structure across all workflow templates.
- **Provisioner**: Updated `luban-provisioner` to use `sys.exit` for proper exit code handling and improved error messaging.
- **Provisioner**: Refactored `utils.py` to prevent shell injection vulnerabilities in secret/configmap copying functions.
- **GitOps**: Updated Dagster GitOps templates to use correct port variables and resource limits/requests for better stability.

### Fixed
- **Promotion**: Resolved "Bad hostname" and "Missing option --git-token" errors in `luban-promotion-workflow-template` by using explicit arguments and static ConfigMap keys.
- **Provisioner**: Fixed `http-route.yaml` port mismatch in Dagster GitOps template.
- **Security**: Added `argo-controller-role.yaml` to the deployment manifest list to ensure correct RBAC for the Argo controller.

## [v0.9.3] - 2026-02-23

### Changed
- **Tooling**: Migrated `luban-provisioner` to use `uv` for dependency management, ensuring faster and more reproducible builds.
- **Tooling**: Updated `luban-provisioner` entrypoint to use `uv run`, improving runtime environment handling.
- **Workflow**: Updated all workflow templates to use the `luban-provisioner` CLI command instead of direct `python3` invocation, fixing `ModuleNotFoundError` issues.
- **Security**: Fixed `workflow-runner` ServiceAccount template to prevent duplicate secret mounting, resolving `401 Unauthorized` errors during kpack image pushing.
- **Documentation**: Updated `README.md`, `docs/ROADMAP.md`, and `docs/requirements.md` to reflect the new tooling architecture.

### Fixed
- **Provisioner**: Pinned `kubectl` version to `v1.35.1` in `luban-provisioner` Dockerfile for stability.
- **GitOps Utils**: Pinned `kubectl` version in `gitops-utils` Dockerfile.

## [v0.9.2] - 2026-02-21

### Added
- **Dagster Support**: Introduced comprehensive support for provisioning and managing a Dagster data orchestration platform.
    - **Platform Provisioning**: New workflow `luban-dagster-platform-setup-template` to deploy a full Dagster instance (Daemon, Webserver, Postgres) with GitOps management.
    - **Code Locations**: New workflow `luban-dagster-code-location-workflow-template` to onboard new data teams/projects with isolated Code Location deployments.
    - **Scaffolding**: Added Cookiecutter templates for Dagster Platform GitOps, Code Location GitOps, and Python Source Code (`luban-dagster-*-template`).
    - **Configuration**: Added `luban-dagster-config` ConfigMap to manage platform-specific settings.
- **Dynamic Pipeline Dispatch**: Implemented `luban-pipeline-dispatcher-template` to dynamically route CI workflows to the correct tenant namespace based on the source Git repository URL.
    - **Azure/GitHub Support**: Automatically parses Organization/Project from Git URLs to determine the target `ci-<project>` namespace.
    - **Event Integration**: Updated `azure-sensor` and `github-sensor` to trigger the dispatcher workflow instead of static pipelines.

### Fixed
- **Dagster Platform**: Corrected typo `nv_config_maps` -> `env_config_maps` in `dagster-instance` ConfigMap template, ensuring environment variables are correctly injected into Job pods.
- **Dagster Platform**: Updated `DAGSTER_HOME` to `/tmp/dagster_home` in ConfigMaps and Volume Mounts to resolve permission issues in read-only container environments.
- **Provisioner**: Fixed potentially broken YAML loading in `utils.py` by switching to `ruamel.yaml`.

### Refactor
- **Cleanup**: Removed unused `BUILDPACK_IMAGE` variable from `builder/Makefile.env`.
- **Cleanup**: Removed unused imports and initialized variables in `luban-provisioner` source code.

## [v0.9.1] - 2026-02-12

### Architecture
- **Configuration**: Unified `luban-config` and provider-specific ConfigMaps (`github-config`, `azure-config`) copying to project namespaces during provisioning. This fixes missing configuration for downstream workflows like promotion.
- **Robustness**: Updated `luban-provisioner` to default to standard Git provider domains (`github.com`, `dev.azure.com`) if configuration is missing, preventing critical failures.

### Changed
- **Workflow**: Enforced explicit `enum` validation (`snd`, `prd`) for the `environment` parameter in `luban-python-app-workflow-template` and `argocd-app-workflow-template`.
- **Workflow**: Added `enum` validation for `git_provider` in `namespace-provision-workflow-template`.
- **Workflow**: Updated all workflow templates to use `luban-provisioner:0.1.55`.
- **Documentation**: Comprehensive update to `README.md` Credentials section, detailing setup for Git Providers, Registries, and optional tools.

### Fixed
- **Promotion**: Resolved `GIT_SERVER` missing error during promotion by ensuring configuration maps are propagated to tenant namespaces.

## [v0.9.0] - 2026-02-11

### Architecture
- **Multi-Provider Support**: Fully enabled support for **Azure DevOps** in addition to GitHub.
  - Implemented Azure DevOps Project creation, Git Repository provisioning, and Webhook configuration.
  - Unified provisioning logic to support both providers seamlessly.

### Changed
- **Provisioning**: Transitioned all initial Git provisioning operations (Project setup, Repo creation, App scaffolding) to use **HTTPS** with embedded tokens, eliminating complex SSH key management in CI/CD containers.
  - *Note*: For kpack builds on Azure DevOps, the workflow automatically converts HTTPS URLs to SSH format (`git@ssh.dev.azure.com...`) to workaround HTTPS authentication limitations with the current kpack buildpack stack. This is handled transparently by the `luban-ci-kpack` workflow.
- **Workflow**: Updated `luban-promotion-workflow-template` to robustly handle optional environment variables (like `AZURE_SERVER`) via shell execution, preventing "Bad hostname" errors.
- **Workflow**: Updated all core workflow templates to use `luban-provisioner:0.1.45`.
- **Policy**: Updated Azure Branch Protection policies to allow Pull Request creators to approve their own changes (`creatorVoteCounts: true`), streamlining development for smaller teams.

### Fixed
- **Azure DevOps**: Resolved "Project not found" race conditions by implementing polling in the Project creation logic, ensuring the project is fully provisioned before subsequent steps run.
- **Azure DevOps**: Fixed Git URL construction in the `promote` command to correctly include the Project path segment (`{org}/{project}/_git/{repo}`), resolving "Project does not exist" errors during promotion.
- **Azure DevOps**: Removed redundant SSH URL injection logic that was causing confusion.

## [v0.8.0] - 2026-02-09

### Architecture
- **Provisioning**: Completed the unification of all provisioning tools into `luban-provisioner` (v0.1.16).
  - Consolidated GitOps repo, source repo, and project namespace provisioning into a single Python application.
  - Replaced fragile shell scripts in workflows with robust Python logic using `requests` and `git` CLI.
  - Implemented native GitHub API integration for repository creation, webhook configuration, and branch protection.

### Changed
- **Workflow**: Updated `luban-python-app-workflow-template`, `gitops-repo-workflow-template`, and `source-repo-workflow-template` to use `luban-provisioner:0.1.16`.
- **Workflow**: Simplified workflow templates by removing complex inline scripts and delegating logic to the provisioner tool.
- **Workflow**: Restored `gitops_utils_image` in `luban-python-app-workflow-template` to support ArgoCD application management steps.
- **Tooling**: Updated `luban-provisioner` Dockerfile to include `git` and `requests` for full standalone capability.

### Fixed
- **Provisioner**: Restored `copy_secrets` utility function to ensure project namespace provisioning correctly copies credentials.
- **CLI**: Fixed missing command-line options in the unified CLI entrypoint.

## [v0.7.0] - 2026-02-09

### Architecture
- **Provisioning**: Unified `gitops-provisioner`, `gitsrc-provisioner`, and `luban-provisioner` into a single monolithic tool `luban-provisioner`.
  - Simplifies maintenance, versioning, and distribution.
  - New modular Python CLI architecture with subcommands (`gitops`, `source`, `project`).
  - Reduced Docker image footprint and unified dependency management (one Dockerfile).

### Changed
- **Workflow**: Updated `gitops-repo-workflow-template`, `source-repo-workflow-template`, and `luban-python-app-workflow-template` to use the new `luban-provisioner:0.1.14` image.
- **Workflow**: Renamed parameters `gitops_provisioner_image` and `gitsrc_provisioner_image` to `luban_provisioner_image` for consistency.
- **Provisioner**: Updated `luban-provisioner` to automatically copy `harbor-creds` (RW) to project namespaces, resolving kpack push authentication issues (`UNAUTHORIZED`).
- **Makefile**: Updated `tools-image-build` and `tools-image-push` targets to reflect the merged toolset.

### Removed
- **Tools**: Deleted deprecated `tools/gitops-provisioner` and `tools/gitsrc-provisioner` directories.

## [v0.6.9] - 2026-02-05

### Changed
- **Infrastructure**: Implemented Global Workflow Defaults in Argo Controller ConfigMap (`argo-workflows-workflow-controller-configmap`) to enforce consistent security and lifecycle policies.
  - **Security**: Globally enforced `runAsNonRoot: true`, `runAsUser: 1000`, and `fsGroup: 1000`.
  - **Cleanup**: Enabled global `ttlStrategy` to automatically delete completed workflows (24h retention) and successful workflows (30m retention).
  - **Cost**: Enabled global `podGC` (`OnPodCompletion`) to immediately delete pods after execution, and set `activeDeadlineSeconds` (1h) to prevent runaway workflows.
- **Refactor**: Removed redundant `securityContext` definitions from all WorkflowTemplates (`luban-project`, `luban-app`, `argocd-*`, `gitops-*`, etc.) in favor of the new global defaults.
- **Cleanup**: Removed `workflow-cleanup-cron.yaml` and `global-workflow-restrictions-rollback.yaml` as the Argo Controller now handles lifecycle management natively.
- **Robustness**: Updated `Makefile` to use `kubectl apply` instead of `kubectl patch` for the global configuration to prevent YAML corruption during deployment.

## [v0.6.8] - 2026-02-05

### Added
- **Promotion**: Implemented "Trunk-Based Promotion" workflow (`luban-promotion-template`), allowing `snd` (develop) to `prd` (main) promotion via direct Pull Requests.

### Changed
- **Workflow**: Updated `luban-ci-kpack-workflow-template` to recursively replace placeholder image names in **all** overlays (`app/overlays/*`) during the initial build, ensuring correct image references for future environment promotions.
- **Refactor**: Renamed `promotion-workflow-template.yaml` to `luban-promotion-workflow-template.yaml` for consistency and simplified its logic to operate directly on the `develop` branch.
- **Documentation**: Updated `README.md` to document the new trunk-based promotion strategy.

## [v0.6.7] - 2026-02-03

### Added
- **Developer Experience**: Added `setup_source_repo` parameter with `yes`/`no` enum to `luban-app-setup-template`, allowing optional source repo provisioning.
- **Developer Experience**: Added `luban-promotion-template` to facilitate environment promotion from `snd` to `prd` via Pull Requests in the GitOps repository.
- **Infrastructure**: Integrated `source-repo-workflow-template.yaml` and `luban-promotion-workflow-template.yaml` into the automated deployment pipeline (Makefile).

### Changed
- **Robustness**: Refactored all workflow templates to use native shell logic instead of complex Argo expressions for parameter derivation (e.g., Git organization fallback, URL construction).
- **Documentation**: Updated `README.md` and planning docs under `docs/` to reflect new architecture and features.

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
- **Workflow**: Removed unused `default_image` parameter from `gitops-repo-workflow-template` and `luban-python-app-workflow-template` interfaces.
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
- **kpack Workflow**: Added the kpack workflow template and related manifests (now located under `manifests/workflows/` and `manifests/kpack/`).
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
