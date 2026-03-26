# Local development (Dagster + dbt + StarRocks source template)

This guide is for Luban developers working on the **source template** and verifying the rendered project locally.

## Render the template

From the repo root:

```bash
make -C tools/luban-provisioner render-template
```

By default the rendered project is written to `$(OUTPUT_DIR)/test_app` (default `OUTPUT_DIR` is `/tmp/luban-rendered`).

## Setup and run the rendered project

```bash
cd /tmp/luban-rendered/test_app
make setup
```

## Start StarRocks (Docker Compose)

```bash
docker compose -f docker/docker-compose.yml up -d
```

Wait until the `starrocks-init` container finishes. It registers the BE into FE.

StarRocks ports exposed locally:

- FE HTTP: `8030`
- FE MySQL: `9030`
- BE HTTP: `8040`

## Configure environment

In the rendered project:

```bash
cp .env.example .env
```

For local StarRocks via Docker Compose, these defaults typically work:

- `STARROCKS_HOST=localhost`
- `STARROCKS_PORT=9030`
- `STARROCKS_USER=root`
- `STARROCKS_PASSWORD=`

## Run Dagster

```bash
make dev
```

Dagster Webserver should be available at `http://localhost:3000`.

## ODS demo data (optional)

Bootstrap:

```bash
make ods-test-bootstrap
```

Append new rows (simulate incremental arrival):

```bash
make ods-test-append
```

## Partitioning notes

The template currently ships with **daily** partition support only.

- Daily partitions are the recommended default for warehouse-scale transactional tables.
- Hourly aggregation models can still be built, but they are typically small enough that hourly partitioning is not required.

