# Dagster + dbt + StarRocks code location template

This documentation describes the **source template**:

- Template source: `tools/luban-provisioner/templates/source/luban-dagster-dbt-starrocks-code-location-source-template/`
- Rendered output: a Dagster code location repo containing `dbt_project/` and `src/<package_name>/`

Notes:

- Examples may contain cookiecutter variables (for example `{{cookiecutter.package_name}}`). In rendered projects, those are replaced with real values.
- Rendered projects do not ship template documentation; their `README.md` links back to this directory.

## Guides

- Usage and architecture: `template_usage.md`
- Developer workflow (jobs/schedules/sensors via `meta.luban.*`): `developer_workflow.md`
- Local development (render + run): `local_development.md`
