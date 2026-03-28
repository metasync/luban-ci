# Dagster Integration

Luban CI provides first-class support for Dagster, enabling data teams to deploy platforms and code locations using GitOps.

## Features

- **Full Platform Provisioning**:
  - Daemon, Webserver, Postgres, and Dagit (UI).
  - GitOps-managed infrastructure.
- **Isolated Code Locations**:
  - Each data team or project can have its own Code Location (User Code Deployment).
  - Deployed as separate Kubernetes deployments, isolated from the platform components.
- **GitOps Workflow**:
  - Infrastructure changes (e.g., resource limits, image versions) are managed via GitOps repositories.

## Dagster Platform Setup

This Workflow bootstraps a full Dagster instance for a team.

- **Template**: [luban-dagster-platform-setup-template.yaml](../../../manifests/workflows/luban-dagster-platform-setup-template.yaml)
- **What it does**:
  1.  **GitOps Repository**: Provisions `<app_name>-gitops` with Dagster Platform Helm/Kustomize base.
  2.  **ArgoCD Application**: Deploys the platform components to the target environment (e.g., `snd-data`).
- **Parameters**:
  - `project_name`: (Required) The team/domain name (e.g., `data-platform`).
  - `app_name`: (Optional) Default: `dagster-platform`.
  - `environment`: (Optional) Default: `snd`.

## Dagster Code Location Setup

This Workflow bootstraps a new Code Location for user code.

- **Template**: [luban-dagster-code-location-workflow-template.yaml](../../../manifests/workflows/luban-dagster-code-location-workflow-template.yaml)
- **What it does**:
  1.  **GitOps Repository**: Provisions `<app_name>-gitops` with Code Location deployment manifests.
  2.  **ArgoCD Application**: Deploys the code location server.
  3.  **Source Code**: (Optional) Scaffolds a new Python repo with Dagster assets/definitions.
- **Parameters**:
  - `project_name`: (Required) The team/domain name.
  - `app_name`: (Required) The name of the code location (e.g., `etl-jobs`).
  - `setup_source_repo`: (Optional) Whether to scaffold source code. Default: `yes`.

### Runtime Configuration (GitOps)

The code location GitOps template wires environment variables into the code-server Deployment via:

- `dagster-env` ConfigMap (optional): shared Dagster platform connection settings.
- `<app_name>-config` ConfigMap: app-specific configuration.
- `<app_name>-secret` Secret (optional): app-specific secrets, typically replicated from `luban-ci`.

For secrets, the `snd`/`prd` overlays include a stub Secret with `replicate-from` so GitOps owns the object metadata while the replicator controller fills the secret data.

## Dagster + dbt (StarRocks) Code Location

For teams using dbt as the transformation engine on StarRocks, Luban CI provides a standardized Dagster code location skeleton that wires Dagster orchestration to dbt execution.

- **Concept**: [dagster-dbt-code-location-template.md](dagster-dbt-code-location-template.md)
