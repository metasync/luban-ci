# Developer workflow (Dagster + dbt + StarRocks)

This template is designed so most orchestration configuration is declared in dbt and discovered via `dbt_project/target/manifest.json`.

## Philosophy (dbt-first, Dagster-orchestrated)

This template follows a division of responsibilities that scales well for warehouse-style transformations:

- **dbt is the transformation layer**: SQL models, tests, sources, and selection primitives (tags/groups) live in dbt.
- **Dagster is the orchestration and observability layer**: schedules, sensors, retries, backfills, run history, and dependency-aware execution live in Dagster.

In practice, this means:

- You declare orchestration intent close to the models (dbt `meta` and tags), not in ad-hoc Python lists.
- Dagster reads the dbt manifest and turns that intent into jobs/schedules/sensors.
- Python config exists as an escape hatch for cases where dbt metadata is not expressive enough.

### Why declare orchestration intent in dbt?

- **Single source of truth** for model ownership and grouping (tags + `meta.luban.*`).
- **Reviewability**: changes to orchestration intent are part of dbt model reviews.
- **Portability**: the manifest is a stable interface between dbt and Dagster.

### What stays out of dbt meta

Keep model execution details in dbt config (materialization strategy, incremental keys), and keep runtime infrastructure in GitOps (resources, env vars, secrets).

## Source of truth

- dbt model/source metadata: `meta.luban.*`
- dbt model tags: used for simple opt-ins (example: `asset_job`)
- Python config files: optional overrides/escape hatches, empty by default

## Quick start

1. Ensure `dbt_project/target/manifest.json` exists.
   - Local: keep `LUBAN_DBT_PREPARE_ON_LOAD=1` (default).
   - CI or explicit: run `dbt deps` and `dbt parse`.
2. Start the code location and verify `Definitions` load.

## Creating jobs

### One model per asset job (recommended for `dwd`)

Add the `asset_job` tag on the model.

```jinja
{% raw %}{{
  config(
    tags=["daily", "asset_job"],
  )
}}{% endraw %}
```

The generated job name is `dbt_<model>_asset_job`.

### Grouped job (recommended for `dws`)

Define `meta.luban.job` (preferably in `schema.yml`).

```yaml
models:
  - name: fact_orders_daily
    meta:
      luban:
        job:
          name: daily_facts_job
```

All models with the same `meta.luban.job.name` are grouped into the same asset job.

Defaults:

- `include_upstream`: `false`
- `partitions`: inferred from model tags (`daily` tag -> daily partitions)

## Creating schedules

Schedules are declared on the model that represents the job’s “anchor”.

Define `meta.luban.asset_schedule`:

```jinja
{% raw %}{{
  config(
    meta={
      'luban': {
        'asset_schedule': {
          'name': 'orders_anchor_daily_schedule',
          'type': 'daily_at',
          'hour': 1,
          'minute': 0,
          'lookback_days': 0,
          'enabled': True
        }
      }
    }
  )
}}{% endraw %}
```

The schedule targets the asset job derived for the same model (via `asset_job` tag, `job:<name>` tag, or `meta.luban.job`).

## Partition-change sensors (late arrivals)

### Detector

Declare `meta.luban.partition_change.detector` on the detector model.

```jinja
{% raw %}{{
  config(
    tags=['daily'],
    meta={
      'luban': {
        'partition_change': {
          'detector': {
            'enabled': True,
            'lookback_days': 7,
            'offset_days': 1,
            'detect_source': {
              'source': 'ods',
              'table': 'orders'
            },
            'partition_date_expr': 'order_datetime',
            'updated_at_expr': 'updated_at'
          }
        }
      }
    }
  )
}}{% endraw %}
```

Defaults:

- `job_name`: derived from the model’s job config (same rule as schedules)
- `minimum_interval_seconds`: `60`
- `name`: `<model>_partition_change_sensor`

### Propagation

Declare propagation on the upstream model.

```jinja
{% raw %}{{
  config(
    meta={
      'luban': {
        'partition_change': {
          'propagate': {
            'enabled': False,
            'name': 'facts_from_orders_partitions_sensor',
            'targets': [
              {'job_name': 'daily_facts_job'}
            ]
          }
        }
      }
    }
  )
}}{% endraw %}
```

Notes:

- `enabled: false` still registers the sensor definition but defaults it to STOPPED.
- The template enables propagation by default on the `orders` model; set `enabled: false` if you want to onboard gradually.
- `LUBAN_PARTITION_CHANGE_PROPAGATOR_MODE=eager` disables propagation sensors entirely.
- Propagation sensors only react to **new** upstream materializations by default. To replay recent upstream partitions after enabling a sensor, set `LUBAN_PARTITION_CHANGE_PROPAGATOR_CATCHUP_DAYS` (for example `7`) before the first time the sensor runs (or after resetting its cursor).

## Source observation (DataVersion)

Define a watermark column for the dbt source table:

```yaml
sources:
  - name: ods
    tables:
      - name: customers
        meta:
          luban:
            observe:
              watermark_column: ods_updated_at
```

This drives observable source assets and the observation job/schedule.

## Optional overrides (escape hatch)

These files default to empty lists and are merged as `AUTO + OVERRIDES`.

- `src/<package_name>/jobs/dbt_config.py` (`DBT_JOB_SPECS`)
- `src/<package_name>/schedules/dbt_config.py` (`DBT_SCHEDULE_SPECS`)
- `src/<package_name>/sensors/dbt_config.py` (`PARTITION_CHANGE_DETECTION_SPECS`, `PARTITION_CHANGE_PROPAGATION_SPECS`)

### `jobs/dbt_config.py`

```python
from .dbt.presets import models_job


DBT_JOB_SPECS: list[dict] = [
    models_job(
        name="daily_facts_job",
        models=["fact_orders_daily", "fact_customer_orders_daily"],
        partitions=None,
    ),
]
```

### `schedules/dbt_config.py`

```python
from .dbt.presets import daily_at


DBT_SCHEDULE_SPECS: list[dict] = [
    daily_at(
        name="orders_anchor_daily_schedule",
        job_name="dbt_orders_asset_job",
        lookback_days=0,
        hour=1,
        minute=0,
        enabled=True,
    ),
]
```

### `sensors/dbt_config.py`

```python
from .partition_change.detector.presets import daily_partition_change
from .partition_change.propagator.presets import partition_change_propagation


PARTITION_CHANGE_DETECTION_SPECS: list[dict] = [
    daily_partition_change(
        name="orders_partition_change_sensor",
        job_name="dbt_orders_asset_job",
        detector_model="orders",
        lookback_days=7,
        offset_days=1,
        enabled=True,
        minimum_interval_seconds=60,
    )
]


PARTITION_CHANGE_PROPAGATION_SPECS: list[dict] = [
    partition_change_propagation(
        name="facts_from_orders_partitions_sensor",
        upstream_dbt_model="orders",
        job_name="daily_facts_job",
        enabled=False,
        minimum_interval_seconds=30,
    )
]
```

## Troubleshooting

- Missing manifest: ensure `LUBAN_DBT_PREPARE_ON_LOAD=1` or run `dbt deps` + `dbt parse`.
- Duplicate names: job and schedule names must be unique after grouping.
- Partition-change sensor finds no partitions: verify `updated_at_expr` and StarRocks connectivity.
