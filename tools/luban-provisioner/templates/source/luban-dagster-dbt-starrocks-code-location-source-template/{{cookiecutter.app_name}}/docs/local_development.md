# Local Development Guide

This guide explains how to run the rendered Dagster + dbt + StarRocks code location locally.

## Prerequisites

- Docker (or OrbStack) with Docker Compose support
- `uv` installed (recommended) or a working Python environment

## Start StarRocks locally

From the rendered project root:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Wait until the `starrocks-init` container finishes. It registers the BE into FE.

StarRocks ports exposed locally:

- FE HTTP: `8030`
- FE MySQL: `9030`
- BE HTTP: `8040`

## Configure environment

Copy `.env.example` to `.env` and adjust if needed:

```bash
cp .env.example .env
```

For local StarRocks via Docker Compose, these defaults typically work:

- `STARROCKS_HOST=localhost`
- `STARROCKS_PORT=9030`
- `STARROCKS_USER=root`
- `STARROCKS_PASSWORD=`

## Run Dagster

From the rendered project root:

```bash
make dev
```

Dagster Webserver should be available at `http://localhost:3000`.

## Generate sample ODS data (optional)

To bootstrap demo ODS data:

```bash
make ods-test-bootstrap
```

To simulate incremental arrival:

```bash
make ods-test-append
```

## Run dbt manually

Examples:

```bash
uv run dbt build --project-dir dbt_project --select tag:ods_test --vars '{"enable_ods_test": true}'
uv run dbt build --project-dir dbt_project --select fact_customer_orders_daily
```

## Partitioning notes

This template ships with daily partition support only.

- Daily partitions are a good default for warehouse-scale transactional tables.
- Hourly aggregation models can still be built, but are usually small enough that hourly partitioning is not required.

