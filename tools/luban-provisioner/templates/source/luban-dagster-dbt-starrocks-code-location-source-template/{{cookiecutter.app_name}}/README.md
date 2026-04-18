# {{cookiecutter.app_name}}

Dagster + dbt (StarRocks) Code Location for {{cookiecutter.app_name}}.

## Quick start

```bash
make setup
make check-db
make dev
```

## dbt project

This scaffold ships an empty `dbt_project/` skeleton.

- Dagster still starts successfully, but it may show no dbt assets until you copy your dbt project into `dbt_project/` (or set `DBT_PROJECT_DIR`).

## Documentation

This rendered project does not ship template docs.

Canonical documentation for the template lives in the `dbt-dagsterizer` repository under:

- `docs/templates/dagster-dbt-starrocks-code-location/README.md`
- `docs/templates/dagster-dbt-starrocks-code-location/template_usage.md`
- `docs/templates/dagster-dbt-starrocks-code-location/developer_workflow.md`
- `docs/templates/dagster-dbt-starrocks-code-location/local_development.md`
