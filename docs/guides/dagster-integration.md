# Dagster integration (Luban CI)

Luban CI provides a GitOps-first way to operate Dagster:

- A shared **Dagster platform** (daemon, webserver, instance storage).
- Multiple isolated **code locations** (user code deployments) owned by teams.

## Concepts and boundaries

### Dagster platform vs code locations

Luban CI deploys Dagster in two layers:

- **Dagster platform**: daemon + webserver + instance storage.
- **Dagster code locations**: user code served by `dagster code-server` (gRPC).

The platform is shared infrastructure; code locations are application repos owned by teams.

### Dagster vs dbt ownership

Use this rule of thumb:

- **dbt owns**: SQL models, tests, sources, selection semantics (tags/groups).
- **Dagster owns**: orchestration (when/what runs), scheduling, sensors, observability, retries.

## What you get

- **Platform provisioning**: bootstraps a complete Dagster instance via GitOps.
- **Isolated code locations**: each code location is its own Kubernetes deployment, decoupled from the platform.
- **GitOps lifecycle**: configuration changes (resources, image versions, env vars) are made in Git and applied by Argo CD.

## Terminology

- **Platform**: Dagster daemon + webserver + instance storage (for example Postgres).
- **Code location**: a repo containing Dagster user code, served via `dagster code-server` (gRPC).

## Platform setup workflow

Use this to bootstrap a full Dagster instance for a team.

- Template: [luban-dagster-platform-setup-template.yaml](../../manifests/workflows/luban-dagster-platform-setup-template.yaml)
- What it does:
  - Provisions a GitOps repo `<app_name>-gitops` containing the Dagster platform base (Helm/Kustomize).
  - Creates/updates an Argo CD application to deploy the platform into the target environment (for example `snd-data`).
- Parameters:
  - `project_name` (required): team/domain name (for example `data-platform`).
  - `app_name` (optional): defaults to `dagster-platform`.
  - `environment` (optional): defaults to `snd`.

## Code location setup workflow

Use this to bootstrap a new code location (user code deployment).

- Template: [luban-dagster-code-location-workflow-template.yaml](../../manifests/workflows/luban-dagster-code-location-workflow-template.yaml)
- What it does:
  - Provisions a GitOps repo `<app_name>-gitops` containing the code location deployment manifests.
  - Creates/updates an Argo CD application to deploy the code-server.
  - Optionally scaffolds a source repo for the code location.
- Parameters:
  - `project_name` (required): team/domain name.
  - `app_name` (required): code location name (for example `etl-jobs`).
  - `setup_source_repo` (optional): defaults to `yes`.

### Runtime configuration (GitOps)

The code location deployment wires runtime configuration into the `dagster code-server` pod via:

- `dagster-env` ConfigMap (optional): shared Dagster platform connection settings.
- `<app_name>-config` ConfigMap: app-specific configuration.
- `<app_name>-secret` Secret (optional): app-specific secrets, typically replicated from `luban-ci`.

For secrets, `snd`/`prd` overlays include a stub Secret with `replicate-from` so GitOps owns the object metadata while the replicator controller fills the secret data.

## Dagster + dbt (StarRocks) code locations

Luban CI scaffolds a minimal Dagster+dbt (StarRocks) code location skeleton.
All template tutorials, samples, and automation docs live in the external `dbt-dagsterizer` repository:

- https://github.com/metasync/dbt-dagsterizer/tree/main/docs/templates/dagster-dbt-starrocks-code-location

