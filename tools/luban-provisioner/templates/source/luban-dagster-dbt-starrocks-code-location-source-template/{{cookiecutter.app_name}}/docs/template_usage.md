# Template usage guide

This repository is a Dagster code location that orchestrates a dbt project on StarRocks.

The template includes:

- dbt models (`dbt_project/`) that build `dwd/*` and `dws/*`
- a Dagster code location (`src/{{cookiecutter.package_name}}/`) that loads dbt assets
- an ODS observation loop (observable source assets + a schedule)
- declarative automation (automation condition sensor + a dbt translator)

## Quick start (local)

From the generated project root:

```bash
make setup
```

Edit `.env` and set StarRocks connection details (used by both dbt and Dagster’s StarRocks observation resource).

Minimum required variables:

- `STARROCKS_HOST`, `STARROCKS_PORT`, `STARROCKS_USER`, `STARROCKS_PASSWORD`
- `STARROCKS_DB`

Optional variables (defaults are in `.env.example`):

- `STARROCKS_ODS_DB`, `STARROCKS_DWD_DB`, `STARROCKS_DWS_DB`
- `DBT_TARGET`, `DBT_PROJECT_DIR`, `DBT_PROFILES_DIR`

dbt environment:

- Supported targets are: `development`, `sandbox`, `production`
- Default target is: `{{ cookiecutter.default_env }}`

Path behavior:

- `DBT_PROJECT_DIR` and `DBT_PROFILES_DIR` can be absolute paths or paths relative to the repo root.

Then validate connectivity and build dbt:

```bash
make check-db
make dbt-deps
export DBT_VARS='{"min_date":"2026-01-02","max_date":"2026-01-03","min_datetime":"2026-01-02 00:00:00","max_datetime":"2026-01-03 00:00:00"}'
make dbt-build
```

Run Dagster:

```bash
make dev
```

Note: `docker/docker-compose.yml` is provided only as an optional local development convenience to spin up a local StarRocks instance. It is not intended for production use.

Notes:

- On startup, Dagster ensures `dbt_project/target/manifest.json` exists by running `dbt deps` + `dbt parse` if needed. Control this via `LUBAN_DBT_PREPARE_ON_LOAD` (defaults to `1`).
- The default daily partitions start date is controlled by `DAGSTER_DAILY_PARTITIONS_START_DATE`.
- The dbt models in this template expect to run in Dagster partitioned mode and will fail fast at execution time if required dbt vars are missing.
- For partitioned runs, Dagster passes dbt variables `min_date`/`max_date` and `min_datetime`/`max_datetime` based on the partition time window.

## How automation works

The template uses **observable source assets** to detect changes in ODS tables, and **automation conditions** to trigger downstream dbt models.

### 1) Observe ODS tables (data version)

Files:

- ODS observation config: `src/{{cookiecutter.package_name}}/assets/automation_config.py`
- ODS observable sources wiring: `src/{{cookiecutter.package_name}}/assets/observable_sources.py`
- ODS observable sources factory: `src/{{cookiecutter.package_name}}/assets/lib/observable_sources_factory.py`
- Observation job: `src/{{cookiecutter.package_name}}/jobs/observations.py`
- Observation schedule: `src/{{cookiecutter.package_name}}/schedules/observations.py`

The observable source assets compute a `DataVersion` by querying StarRocks:

```sql
select max(<watermark_column>) from <ods_db>.<table>
```

When that value changes, Dagster records a new observation event for the source asset.

### 2) Trigger DWD dbt models

Files:

- dbt asset loading: `src/{{cookiecutter.package_name}}/assets/dbt.py`
- dbt translator: `src/{{cookiecutter.package_name}}/assets/lib/dbt_translator.py`

The dbt translator assigns `AutomationCondition.eager()` to selected dbt models under the `dwd/` folder.
When Dagster detects the upstream ODS source asset has a newer data version, the automation sensor can request a run to materialize the affected downstream assets.

The template also assigns `AutomationCondition.eager()` to DWS dimension models (models under `dws/` tagged `dim`).
This enables dimension refresh (for example `dws.dim_customer`) when upstream inputs (for example `dwd.customers`) change.

### 3) Automation condition sensor

File:

- `src/{{cookiecutter.package_name}}/sensors/__init__.py`

The template defines an `AutomationConditionSensorDefinition` and enables it by default for new deployments.

## What to configure

### Automation target list (ODS tables to observe)

Edit:

- `src/{{cookiecutter.package_name}}/assets/automation_config.py`

```python
AUTOMATION_OBSERVABLE_SOURCES = [
    {
        "source": "ods",
        "table": "customers",
        "watermark_column": "ods_updated_at",
    },
    {
        "source": "ods",
        "table": "orders",
        "watermark_column": "ods_updated_at",
    },
]
```

Spec schema:

- `source`: dbt source name (default example uses `ods`)
- `table`: table name under that source
- `watermark_column`: column used to compute `DataVersion` via `max(...)`

Behavior:

- Each entry creates one observable source asset that queries:
  `select max(<watermark_column>) from <ods_db>.<table>`.
- The translator uses this table list to decide which `models/dwd/*` assets get eager automation.

Assumption:

- The dbt model name in `models/dwd/` matches the table name (e.g. `customers`, `orders`).

If your DWD model naming differs (e.g. `dwd_orders`), update the mapping logic in `assets/lib/dbt_translator.py`.

### Watermark column

Each `watermark_column` should be a monotonically non-decreasing ingestion timestamp (typical CDC columns: `ods_updated_at`, `ingested_at`, `cdc_timestamp`).

If you want a stronger signal than a single timestamp, change the query in `assets/lib/observable_sources_factory.py` (for example: combine `max(ods_updated_at)` with `count(*)`).

### StarRocks query resource

File:

- `src/{{cookiecutter.package_name}}/resources/starrocks.py`

This resource is used only for observation queries (not for dbt execution). It connects using the MySQL protocol and runs small scalar queries like `max(...)`.

Environment variables:

- `STARROCKS_HOST`, `STARROCKS_PORT`, `STARROCKS_USER`, `STARROCKS_PASSWORD`
- `STARROCKS_ODS_DB` (schema/database name containing ODS tables)

dbt runtime stability/tuning:

- `STARROCKS_USE_PURE` (default `true`): forces the pure-Python MySQL connector implementation. Useful to avoid potential crashes in the mysql-connector C extension.
- `DBT_THREADS` (default `4`): overrides dbt thread concurrency.

dbt manifest generation:

- `LUBAN_DBT_PREPARE_ON_LOAD` (default `1`): if `dbt_project/target/manifest.json` is missing, the code location will run `dbt deps` and `dbt parse` on import to generate it.

### StarRocks database mapping

- `STARROCKS_ODS_DB`, `STARROCKS_DWD_DB`, `STARROCKS_DWS_DB` are full StarRocks database names.
- `STARROCKS_DB` is the default working database for this code location (used as the default dbt target schema). By default it matches `STARROCKS_DWS_DB`.

dbt schema behavior:

- This template overrides dbt's default schema concatenation so a model's configured `schema` is used verbatim (StarRocks databases), instead of `target_schema_custom_schema`.

Folder conventions:

- Models under `models/dwd/` are routed to `STARROCKS_DWD_DB`.
- Models under `models/dws/` and all `snapshots/` are routed to `STARROCKS_DWS_DB`.
- Anything else falls back to `target.schema`.

## Jobs and schedules included

- `dbt_daily_facts_job`: materializes the daily facts + upstream dependencies
- `daily_facts_schedule`: runs `dbt_daily_customer_facts_job` at `0 1 * * *`
- `observe_sources_job`: observes only configured source assets
- `observe_sources_schedule`: runs `observe_sources_job` on a configurable cron (default `*/5 * * * *`, configured via `LUBAN_OBSERVE_SOURCES_CRON`)

You can change schedule cadences in `src/{{cookiecutter.package_name}}/schedules/`.

### dbt jobs/schedules config

dbt jobs and dbt schedules are configured as lists:

- `src/{{cookiecutter.package_name}}/jobs/dbt_config.py`
- `src/{{cookiecutter.package_name}}/schedules/dbt_config.py`

This allows adding new manual/ad-hoc or scheduled dbt jobs by editing configuration rather than editing selection logic.

To keep the bar low for non-platform users, these config files use small helper functions:

- `src/{{cookiecutter.package_name}}/jobs/lib/dbt_job_presets.py`
- `src/{{cookiecutter.package_name}}/schedules/lib/dbt_schedule_presets.py`

### Orchestration-level daily lookback (intraday vs finalize)

This template standardizes on orchestration-level lookback for late-arriving updates.

Instead of widening the date range inside a single dbt run, the schedule emits multiple partitioned runs (one per day). This keeps each run bounded to a single daily partition and makes dbt models simpler.

In dbt, models should use the Dagster-provided partition window vars (`min_date`/`max_date`) via the provided macro:

```jinja
{% raw %}{% set w = luban_partition_window_date() %}{% endraw %}
```

In Dagster, schedules can emit multiple partition runs in one schedule tick using `daily_at(..., lookback_days=N)`.

For hourly schedules, use `hourly_at(..., lookback_hours=N)` to run the current hour and prior hours.

To enable hourly partitioned jobs, set `DAGSTER_HOURLY_PARTITIONS_START_DATE` (default: `2026-01-01-00:00`).

Partition mapping rules:

- A dbt model tagged `daily` maps to Dagster daily partitions.
- A dbt model tagged `hourly` maps to Dagster hourly partitions.
- You can also explicitly list model names in `src/{{cookiecutter.package_name}}/assets/automation_config.py` via `DAGSTER_DAILY_PARTITIONED_MODELS` / `DAGSTER_HOURLY_PARTITIONED_MODELS`.

If you see `DagsterDbtManifestNotFoundError` during local development, ensure `LUBAN_DBT_PREPARE_ON_LOAD=1` (default in `.env.example`) so the code location prepares `dbt_project/target/manifest.json` automatically.

### ODS test data (optional)

This template includes optional ODS test models that can generate `ods.customers` and `ods.orders` on demand using dbt models (no seeds required).

They are disabled by default and must be explicitly enabled:

```bash
uv run dbt run --full-refresh --project-dir dbt_project --select tag:ods_test --vars '{"enable_ods_test": true}'
```

Or use the repository Makefile:

```bash
make ods-test-bootstrap
```

Default ODS test knobs (override via `--vars`):

- `enable_ods_test` (default `false`)
- `ods_test_customers_count` (default `500`)
- `ods_test_customers_append_count` (default `0`)
- `ods_test_orders_per_customer` (default `20`)
- `ods_test_orders_append_count` (default `1000`)
- `ods_test_days` (default `30`)
- `ods_test_base_ts` (default empty; uses `current_timestamp()`)

Append mode (simulate new data arrival):

```bash
make ods-test-append
```

Schedules:

- `daily_facts_schedule` targets `dbt_daily_customer_facts_job` by default.
- `orders_daily_schedule` targets `dbt_orders_daily_job` by default and runs with `lookback_days=1`.
- `orders_hourly_schedule` targets `dbt_orders_hourly_job` (hourly partitions) and is disabled by default.

Enable intraday refresh by setting `enabled=True` for `orders_hourly_schedule` in `src/{{cookiecutter.package_name}}/schedules/dbt_config.py`.

#### Example: add a new dbt job

Edit `src/{{cookiecutter.package_name}}/jobs/dbt_config.py`:

```python
from .lib.dbt_job_presets import dbt_cli_build_job, key_prefix_job, models_job


DBT_JOB_SPECS = [
    key_prefix_job(name="dbt_assets_job", prefix="dbt"),
    models_job(
        name="dbt_daily_facts_job",
        models=["fact_orders_daily", "fact_customer_orders_daily"],
        include_upstream=True,
    ),
    dbt_cli_build_job(
        name="dbt_orders_hourly_job",
        models=["fact_orders_hourly"],
        include_upstream=True,
        partitions="hourly",
    ),
]
```

Note: `prefix="dbt"` targets assets whose Dagster asset key starts with `dbt/...`.

#### Example: add/enable a schedule

Edit `src/{{cookiecutter.package_name}}/schedules/dbt_config.py`:

```python
from .lib.dbt_schedule_presets import daily_at, hourly_at


DBT_SCHEDULE_SPECS = [
    daily_at(
        name="daily_facts_schedule",
        job_name="dbt_daily_facts_job",
        lookback_days=0,
        hour=1,
        minute=0,
        enabled=True,
    ),
    hourly_at(
        name="hourly_orders_schedule",
        job_name="dbt_orders_hourly_job",
        lookback_hours=0,
        minute=0,
        enabled=True,
    ),
]
```
