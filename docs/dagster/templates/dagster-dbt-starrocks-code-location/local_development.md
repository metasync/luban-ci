# Local development (template and rendered project)

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

## ODS demo data (optional)

If you plan to use the built-in ODS observation loop and automation, create the demo ODS tables before starting Dagster.

Bootstrap:

```bash
make ods-test-bootstrap
```

Append new rows (simulate incremental arrival):

```bash
make ods-test-append
```

## Run Dagster

```bash
make dev
```

Dagster Webserver should be available at `http://localhost:3000`.

## Partitioning notes

The template currently ships with **daily** partition support only.
