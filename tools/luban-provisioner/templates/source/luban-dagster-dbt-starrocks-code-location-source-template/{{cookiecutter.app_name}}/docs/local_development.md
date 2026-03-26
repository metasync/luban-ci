# Local Development Guide

This guide explains how to run the rendered Dagster + dbt + StarRocks code location locally.

## Prerequisites

- Docker (or OrbStack) with Docker Compose support
- `uv` installed (recommended) or a working Python environment

## Setup

From the rendered project root:

```bash
make setup
```

## Start StarRocks locally

From the rendered project root:

```bash
make docker-up
```

Wait until the `starrocks-init` container finishes. It registers the BE into FE.

StarRocks ports exposed locally:

- FE HTTP: `8030`
- FE MySQL: `9030`
- BE HTTP: `8040`

## Configure environment

`make setup` creates `.env` if missing. Update it with your StarRocks connection values.

For local StarRocks via Docker Compose, these defaults typically work:

- `STARROCKS_HOST=localhost`
- `STARROCKS_PORT=9030`
- `STARROCKS_USER=root`
- `STARROCKS_PASSWORD=`

Validate connectivity:

```bash
make check-db
```

## Generate sample ODS data (optional)

If you plan to use the built-in ODS observation loop and automation, create the demo ODS tables before starting Dagster.

To bootstrap demo ODS data:

```bash
make ods-test-bootstrap
```

To simulate incremental arrival:

```bash
make ods-test-append
```

## Run Dagster

From the rendered project root:

```bash
make dev
```

Dagster Webserver should be available at `http://localhost:3000`.

## Run dbt manually

Examples:

```bash
make dbt-deps
export DBT_VARS='{"min_date":"2026-01-02","max_date":"2026-01-03","min_datetime":"2026-01-02 00:00:00","max_datetime":"2026-01-03 00:00:00"}'
make dbt-build
```

## Partitioning notes

This template ships with daily partition support only.

- Daily partitions are a good default for warehouse-scale transactional tables.
- Hourly aggregation models can still be built, but are usually small enough that hourly partitioning is not required.
