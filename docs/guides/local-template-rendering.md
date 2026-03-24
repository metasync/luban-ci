# Local Template Rendering (Developer Tutorial)

This guide shows how to render a local source-code project from a Luban Provisioner template (default: `luban-dagster-dbt-starrocks-code-location-source-template`) and how to bootstrap the rendered project to run Dagster + dbt.

## Prerequisites

- `uv` installed and available on your PATH
- Python 3.12+ (the templates typically use 3.12)
- Optional (only if you want a local StarRocks): Docker + Docker Compose

## 1) Pick a template

List templates:

```bash
make -C tools/luban-provisioner list-templates
```

The current default used by `make render-template` is:

- `luban-dagster-dbt-starrocks-code-location-source-template`

## 2) Render a project

### Option A (quick smoke render)

This renders the default template into `/tmp/luban-rendered/test_app`:

```bash
make -C tools/luban-provisioner render-template
```

### Option B (render your own app name)

If you want a real project name (recommended), run Cookiecutter directly so you can control the output directory and template variables.

Example:

```bash
OUTPUT_DIR=/tmp/luban-rendered
TEMPLATE=luban-dagster-dbt-starrocks-code-location-source-template

uv run cookiecutter --no-input -f -o "$OUTPUT_DIR" "tools/luban-provisioner/templates/source/$TEMPLATE" \
  project_name="My Project" \
  app_name="my_app" \
  package_name="my_app" \
  dagster_version="1.12.19" \
  author_name="Your Name" \
  author_email="you@example.com"
```

Your rendered project will be at:

- `/tmp/luban-rendered/my_app`

## 3) Bootstrap the rendered project

Move into the rendered project:

```bash
cd /tmp/luban-rendered/my_app
```

Create `.env` and install dependencies:

```bash
make setup
```

## 4) Provide a StarRocks database

You have two options:

### Option A: use an existing StarRocks

Edit `.env` and set your connection values:

- `STARROCKS_HOST`
- `STARROCKS_PORT` (default `9030`)
- `STARROCKS_USER` (default `root`)
- `STARROCKS_PASSWORD`

### Option B: start local StarRocks with docker (optional, local dev only)

The template includes `docker/docker-compose.yml` to start StarRocks locally when needed. This is not intended for production use.

```bash
make docker-up
```

Then keep `STARROCKS_HOST=localhost` and `STARROCKS_PORT=9030` in `.env`.

To stop it:

```bash
make docker-down
```

## 5) Verify connectivity

```bash
make check-db
```

## 6) Bootstrap ODS mock/test data (recommended)

Many examples and jobs expect ODS databases/tables to exist. If you are starting from a fresh local StarRocks, bootstrap the synthetic ODS test data first.

```bash
make ods-test-bootstrap
```

To generate additional synthetic ODS data later:

```bash
make ods-test-append
```

## 7) Run Dagster locally

```bash
make dev
```

Open Dagster:

- `http://localhost:3000`

## 8) Run dbt (optional)

The template’s dbt jobs are designed for Dagster-partitioned execution and expect partition window vars.

Example:

```bash
export DBT_VARS='{"min_date":"2026-01-02","max_date":"2026-01-03","min_datetime":"2026-01-02 00:00:00","max_datetime":"2026-01-03 00:00:00"}'
make dbt-build
```

## Troubleshooting

- Manifest missing / `DagsterDbtManifestNotFoundError`:
  - Keep `LUBAN_DBT_PREPARE_ON_LOAD=1` (default in `.env.example`). When `dbt_project/target/manifest.json` is missing, the code location runs `dbt deps` + `dbt parse` on import to generate it.
