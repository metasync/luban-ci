# {{cookiecutter.app_name}}

Dagster + dbt (StarRocks) Code Location for {{cookiecutter.app_name}}.

For a detailed guide on automation, observation, and template configuration, see `docs/template_usage.md`.

## Getting Started

### Design Principles

#### Incremental Processing with Dagster Partitions
We recommend using **Incremental Materialization driven by Dagster Partitions** for large fact tables instead of dbt's native `microbatch` strategy.

**Why?**
1. **Control & Observability**: Dagster partitions provide granular visibility in the UI. You can see exactly which time slices (e.g., days) have succeeded or failed and retry them individually.
2. **Idempotency**: Backfilling a specific partition range in Dagster is robust and idempotent. It replaces data only for the requested time window, avoiding accidental data duplication or full table scans.
3. **Orchestrator-Driven**: By lifting the partitioning logic to the orchestrator (Dagster), the data pipeline becomes a series of discrete, manageable units of work rather than a black-box process.

**Implementation Pattern:**
In your dbt model:
```sql
{% raw %}{{
    config(
        materialized='incremental',
        unique_key='order_id'
    )
}}{% endraw %}

select ...
from {% raw %}{{ source('ods', 'orders') }}{% endraw %}

{% raw %}{% if is_incremental() %}
    -- Dagster automatically injects these variables for partitioned runs
    where order_datetime >= '{{ var("min_datetime") }}'
      and order_datetime < '{{ var("max_datetime") }}'
{% endif %}{% endraw %}
```

#### Non-Time-Based Partitions
While time-based partitioning is standard, Dagster also supports non-time-based dimensions (e.g., partitioning by `country` or `tenant_id`) using `StaticPartitionsDefinition` or `DynamicPartitionsDefinition`.

**How it works:**
1. Define the custom partition definition in your Dagster assets (e.g., `assets/dbt.py`).
2. Update `assets/lib/dbt_translator.py` to map this definition to the specific dbt models.
3. In your dbt SQL, Dagster injects the current partition key via the `dagster_partition_key` variable.

**Example dbt implementation:**
```sql
{% raw %}{% if is_incremental() %}
    -- Filter source data to the specific partition slice (e.g., 'US', 'UK')
    where country_code = '{{ var("dagster_partition_key") }}'
{% endif %}{% endraw %}
```

### Installation & Local Setup

We use a `Makefile` to simplify local development setup. Run the following command to initialize your virtual environment, install dependencies, and create your local `.env` file:

```bash
make setup
```

Once complete, open the newly created `.env` file in the root of the project and fill in your local StarRocks connection details.

After filling out the `.env` file, you can test your database connectivity by running:

```bash
make check-db
```

When you run Dagster locally, it will automatically load the variables from this `.env` file. By default, `DBT_TARGET` is set to `{{ cookiecutter.default_env }}`, which triggers dbt to use the matching profile configuration.

### Configure StarRocks connection (Manual)

If you prefer not to use `.env` or are deploying to a server, you can set the environment variables manually.


Supported dbt targets:

`development`, `sandbox`, `production`

```bash
export STARROCKS_HOST=127.0.0.1
export STARROCKS_PORT=9030
export STARROCKS_USER=root
export STARROCKS_PASSWORD=""
export STARROCKS_ODS_DB={{cookiecutter.app_name}}_ods_dev
export STARROCKS_DWD_DB={{cookiecutter.app_name}}_dwd_dev
export STARROCKS_DWS_DB={{cookiecutter.app_name}}_dws_dev

# Working/default database for this code location. By default it matches DWS.
export STARROCKS_DB={{cookiecutter.app_name}}_dws_dev

# ODS/DWD/DWS env vars are full StarRocks database names.

# Select dbt target
export DBT_TARGET={{ cookiecutter.default_env }}

# Optional: tune timeouts (defaults shown)
export STARROCKS_PLANNER_OPTIMIZE_TIMEOUT_MS=300000
export STARROCKS_QUERY_TIMEOUT_SECONDS=3600
```

### Run dbt

Instead of passing the `--project-dir` and `DBT_PROFILES_DIR` every time, you can use the built-in `Makefile` targets:

```bash
# Install dbt dependencies
make dbt-deps

# Build the entire dbt project (run models + execute tests)
make dbt-build

# Run the dbt project without testing
make dbt-run
```

### ODS source mapping

The `dwd` layer reads raw tables from the `ods` source (see `dbt_project/models/dwd/sources.yml`).
You can override the ODS schema and physical table identifiers using dbt vars:

```bash
uv run dbt build --project-dir ./dbt_project \
  --vars '{"ods_schema": "ods"}'
```

If vars are not provided, the template defaults are sourced from environment variables defined in `dbt_project.yml`.

Convention: ODS table `name` matches the physical table name. If you need a different physical name, set `identifier` in `dwd/sources.yml`.

### Run Dagster

```bash
make dev
```

### Running Tests

We use `pytest` for testing Dagster definitions and assets.

```bash
make test
```
