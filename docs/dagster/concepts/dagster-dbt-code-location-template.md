# Dagster + dbt (StarRocks) Code Location Template

For the end-to-end developer workflow (concepts + templates + local validation), start with:

- `docs/dagster/handbook.md`

Luban CI supports deploying Dagster in two layers:

- **Dagster Platform**: Webserver + Daemon + Dagster instance storage.
- **Dagster Code Location**: User code served by `dagster code-server` (gRPC).

This document describes the standard **Dagster + dbt (StarRocks) code location** source template intended for data transformation teams.

## Goal

Provide a runnable, opinionated skeleton that:

- Keeps the Dagster platform and code locations decoupled.
- Uses **dbt** as the transformation engine (SQL/models/tests).
- Uses **Dagster** for orchestration, scheduling, observability, and dependency management.
- Standardizes folder structure and wiring so teams focus on datasets and models.

## When to Use This Template

Use this template when:

- You want a new Dagster code location that primarily materializes dbt assets.
- You want consistent conventions across teams (layout, naming, local run, CI expectations).

Do not use this template when:

- You need a Dagster platform (use the Dagster platform workflow/template).
- Your pipeline is mostly non-dbt (pure Python ops, Spark jobs, etc.).

## Boundary: Dagster vs dbt

### dbt owns

- Model definitions (SQL in `models/`).
- Data tests (schema tests, custom tests).
- Sources/exposures/macros/packages.
- Model selection semantics (`--select`, tags, state).

### Dagster owns

- Asset orchestration (when/what to run).
- Observability (asset-level logs, lineage view, run history).
- Scheduling, sensors, retries, alerting.
- Coordination with non-dbt assets (ingestion, external tables, ML training).

## Repository Layout

The template is a single Git repo representing **one** code location.

- `src/<package_name>/` Dagster code location module
  - `definitions.py` exports `defs` (Dagster entrypoint)
  - `assets/dbt.py` defines how dbt is exposed as Dagster assets
- `dbt_project/` dbt project
  - `dbt_project.yml`
  - `models/` (standard dbt structure)
    - `models/dwd/` Data Warehouse Details layer
    - `models/dws/` Data Warehouse Service layer
  - `seeds/`, `macros/` (standard dbt structure)
  - `profiles.yml` (local-safe default)

## Runtime Contract (Luban CI + Dagster)

Luban CI deploys code locations as a Kubernetes Deployment that runs:

`dagster code-server start -h 0.0.0.0 -p <port> -m <package_name>`

Notes:

- `package_name` is the Python-module-safe form of `app_name` (for example `test-app` → `test_app`).

This implies:

- The Python module `<package_name>` must import successfully.
- The module must expose `defs` (via `__init__.py`).

## Local Development

For the end-to-end local workflow (render template, start StarRocks, run Dagster), see:

- `docs/dagster/templates/dagster-dbt-starrocks-code-location/local_development.md`

## Production Configuration Guidance

- Keep secrets out of Git.
- Prefer configuring warehouse credentials via environment variables and/or mounted Secrets.
- For production adapters (e.g., Snowflake, BigQuery, Postgres, StarRocks), update `dbt_project/profiles.yml` to use the adapter and reference credentials via `env_var()`.

## Environments

This template supports configuring the default dbt environment via Cookiecutter (`default_env`).

Common mapping:

- `sandbox`: developer environment and Luban CI `snd` deployment
- `production`: Luban CI `prd` deployment

Set `DBT_TARGET` to one of the configured environments. In GitOps deployments, you typically keep env var names the same and just provide different values per environment.

In GitOps, the code location template sets:

- `snd`: `DBT_TARGET=sandbox`
- `prd`: `DBT_TARGET=production`

## Layers as Separate Databases (StarRocks)

In many StarRocks deployments, `ods`, `dwd`, and `dws` are separate databases on the same cluster.
In this setup:

- dbt models are built into the target database configured by `STARROCKS_DB`.
- The `ods` source is mapped via `dbt_project/models/dwd/sources.yml`.

The template centralizes layer mapping in `dbt_project.yml` using env-var-driven dbt `vars`:

- `ods_schema` defaults from `STARROCKS_ODS_DB`
- `dwd_schema` defaults from `STARROCKS_DWD_DB` (fallback: `dwd`)
- `dws_schema` defaults from `STARROCKS_DWS_DB` (fallback: `dws`)

By default, `STARROCKS_DWD_DB` falls back to `dwd` and `STARROCKS_DWS_DB` falls back to `dws`.

You can override ODS schema mapping at runtime with `--vars` (e.g., `ods_schema`) when needed.

Convention: ODS source table `name` matches the physical table name. If you need a different physical name, set `identifier` in `dwd/sources.yml`.

### Naming Convention

In both local `.env.example` and GitOps overlays, the default StarRocks database names are prefixed with `package_name` (not raw `app_name`) to ensure identifier-safe defaults.

## Recommended Conventions

- **One code location per domain**: e.g. `master-data` and `retail-analytics` are separate repos/code locations.
- **Shared dimensions as a producer**: master data pipelines publish shared dimensions that other code locations consume.
- **dbt-first transformations**: use Dagster to orchestrate dbt and add non-dbt assets only when necessary.
- **Stable selection semantics**: define tags/groups in dbt and use them consistently in Dagster jobs/schedules.

For the supported orchestration metadata schema (`meta.luban.*`) and the intended developer workflow, see:

- `docs/dagster/templates/dagster-dbt-starrocks-code-location/developer_workflow.md`

## Extending the Skeleton

Common extensions that keep the boundary clean:

- Add ingestion assets in Dagster that produce dbt sources, then make dbt depend on them.
- Add partitioning in Dagster for incremental models, passing partition ranges into dbt via `--vars`.
- Add asset checks for dbt tests to show failures at the asset level.
