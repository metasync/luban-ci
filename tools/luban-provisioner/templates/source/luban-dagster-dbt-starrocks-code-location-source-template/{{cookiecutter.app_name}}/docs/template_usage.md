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
make dbt-build
```

Run Dagster:

```bash
make dev
```

Notes:

- On startup, the dbt assets module may run dbt to prepare `manifest.json`. You can disable this by setting `LUBAN_DBT_PREPARE_IF_DEV=false`.
- The default daily partitions start date is controlled by `DAGSTER_DAILY_PARTITIONS_START_DATE`.

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

### StarRocks database mapping

- `STARROCKS_DB`: the default database/schema used by dbt connection (see `dbt_project/profiles.yml`)
- `STARROCKS_ODS_DB`: where dbt reads sources (and where observation queries run)
- `STARROCKS_DWD_DB`: where `models/dwd/*` materialize
- `STARROCKS_DWS_DB`: where `models/dws/*` materialize

## Jobs and schedules included

- `dbt_daily_facts_job`: materializes the daily facts + upstream dependencies
- `daily_facts_schedule`: runs `dbt_daily_customer_facts_job` at `0 1 * * *`
- `observe_sources_job`: observes only configured source assets
- `observe_sources_schedule`: runs `observe_sources_job` every minute (`* * * * *`)

You can change schedule cadences in `src/{{cookiecutter.package_name}}/schedules/`.

### dbt jobs/schedules config

dbt jobs and dbt schedules are configured as lists:

- `src/{{cookiecutter.package_name}}/jobs/dbt_config.py`
- `src/{{cookiecutter.package_name}}/schedules/dbt_config.py`

This allows adding new manual/ad-hoc or scheduled dbt jobs by editing configuration rather than editing selection logic.

To keep the bar low for non-platform users, these config files use small helper functions:

- `src/{{cookiecutter.package_name}}/jobs/lib/dbt_job_presets.py`
- `src/{{cookiecutter.package_name}}/schedules/lib/dbt_schedule_presets.py`

### Parameterized daily fact lookback (intraday vs finalize)

The template includes two examples:

- A daily fact that is scheduled once per day and uses a fixed microbatch lookback (example: `fact_customer_orders_daily`).
- A daily fact that supports intraday refresh and end-of-day finalize by parameterizing microbatch lookback (example: `fact_orders_daily`).

The parameterized daily fact uses a dbt var for microbatch lookback:

```jinja
lookback=var("daily_fact_lookback", 1)
```

Behavior:

- Intraday runs set `daily_fact_lookback=0` to avoid reprocessing older days.
- Finalize runs set `daily_fact_lookback=1` (or higher) to catch late-arriving updates.

In Dagster, the template provides two jobs:

- `dbt_intraday_orders_daily_job`: runs `dbt build` with `--vars '{"daily_fact_lookback": 0}'`
- `dbt_finalize_orders_daily_job`: runs `dbt build` with `--vars '{"daily_fact_lookback": 1}'`

Schedules:

- `daily_facts_schedule` targets `dbt_daily_customer_facts_job` by default.
- `finalize_orders_daily_schedule` targets `dbt_finalize_orders_daily_job` by default.
- `intraday_orders_daily_schedule` targets `dbt_intraday_orders_daily_job` and is disabled by default.

Enable intraday refresh by setting `enabled=True` for `intraday_orders_daily_schedule` in `src/{{cookiecutter.package_name}}/schedules/dbt_config.py`.

#### Example: add a new dbt job

Edit `src/{{cookiecutter.package_name}}/jobs/dbt_config.py`:

```python
from .lib.dbt_job_presets import key_prefix_job, models_job


DBT_JOB_SPECS = [
    key_prefix_job(name="dbt_assets_job", prefix="dbt"),
    models_job(
        name="dbt_daily_facts_job",
        models=["fact_orders_daily", "fact_customer_orders_daily"],
        include_upstream=True,
    ),
    models_job(
        name="dbt_hourly_orders_job",
        models=["fact_orders_daily"],
        include_upstream=True,
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
        hour=1,
        minute=0,
        enabled=True,
    ),
    hourly_at(
        name="hourly_orders_schedule",
        job_name="dbt_hourly_orders_job",
        minute=0,
        enabled=True,
    ),
]
```
