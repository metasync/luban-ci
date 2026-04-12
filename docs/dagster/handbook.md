# Dagster development handbook (Luban CI)

This handbook is the entry point for Luban developers and data teams working with Dagster on Luban CI.
It covers the platform vs code-location boundary, how to use the Dagster + dbt (StarRocks) code location template, and how to develop and validate changes.

## 1) Concepts and boundaries

### Dagster platform vs code locations

Luban CI deploys Dagster in two layers:

- **Dagster platform**: daemon + webserver + instance storage.
- **Dagster code locations**: user code served by `dagster code-server` (gRPC).

The platform is shared infrastructure; code locations are application repos owned by teams.

### Dagster vs dbt ownership

Use this rule of thumb:

- **dbt owns**: SQL models, tests, sources, selection semantics (tags/groups).
- **Dagster owns**: orchestration (when/what runs), scheduling, sensors, observability, retries.

In this template, orchestration signals are declared in dbt and discovered from `manifest.json`.

## 2) Templates on Luban CI

Luban CI provides a Dagster code location workflow template and a source code template.

- Dagster integration overview: `concepts/dagster-integration.md`
- Dagster + dbt (StarRocks) template overview: `concepts/dagster-dbt-code-location-template.md`

## 3) Dagster + dbt + StarRocks code location template

Canonical documentation lives under:

- `docs/dagster/templates/dagster-dbt-starrocks-code-location/`

Start here:

- Template overview: `docs/dagster/templates/dagster-dbt-starrocks-code-location/README.md`
- Developer workflow (`meta.luban.*`): `docs/dagster/templates/dagster-dbt-starrocks-code-location/developer_workflow.md`
- Local development (render + run): `docs/dagster/templates/dagster-dbt-starrocks-code-location/local_development.md`

## 4) Local development checklist (template maintainers)

Use this when changing template code or docs.

### Render the template

```bash
make -C tools/luban-provisioner render-template
```

### Validate the rendered code location

From the rendered project directory:

```bash
uv sync
make dbt-parse
uv run pytest -q tests/test_definitions.py::test_definitions_load
```

If you need StarRocks for deeper validation, follow:

- `docs/dagster/templates/dagster-dbt-starrocks-code-location/local_development.md`

## 5) How the template is configured (high level)

### Source of truth

- dbt metadata: `meta.luban.*`
- dbt tags: simple opt-ins (example: `asset_job`)
- Python config files: optional overrides (escape hatch), merged as `AUTO + OVERRIDES`

### Orchestration features

- Asset jobs: per-model (`asset_job` tag) and grouped (`meta.luban.job`).
- Asset schedules: `meta.luban.asset_schedule` (targets the model’s derived asset job).
- Partition-change: `meta.luban.partition_change.detector` and `.propagate`.
- ODS observation: `meta.luban.observe` on dbt sources.

## 6) Recommended doc structure

To keep docs easy to follow:

- Keep this handbook as the main entry point.
- Keep template-specific details under `docs/dagster/templates/<template-name>/`.
- Keep one-off operational topics under `docs/guides/` (cluster, RBAC, webhook testing).
