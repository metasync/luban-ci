import os
import json

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir, get_dbt_profiles_dir
from .lib.partition_vars import _get_dbt_vars_for_context
from .lib.dbt_translator import LubanDagsterDbtTranslator

daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-01-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

dbt_project_dir = get_dbt_project_dir()
dbt_profiles_dir = get_dbt_profiles_dir()
dbt_target = os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}")


def _stub_manifest() -> dict:
    project_name = "{{cookiecutter.package_name}}_dbt"

    def model(unique_id: str, name: str, fqn: list[str], depends_on: list[str], tags: list[str] | None = None):
        return {
            "unique_id": unique_id,
            "resource_type": "model",
            "name": name,
            "package_name": project_name,
            "fqn": fqn,
            "tags": tags or [],
            "depends_on": {"nodes": depends_on},
            "config": {"enabled": True, "materialized": "table"},
            "meta": {},
            "original_file_path": "models/stub.sql",
        }

    def source(unique_id: str, source_name: str, table_name: str):
        return {
            "unique_id": unique_id,
            "resource_type": "source",
            "source_name": source_name,
            "name": table_name,
            "package_name": project_name,
            "fqn": [project_name, source_name, table_name],
            "tags": [],
            "depends_on": {"nodes": []},
            "config": {"enabled": True},
            "meta": {},
            "original_file_path": "models/stub.yml",
        }

    src_customers = f"source.{project_name}.ods.customers"
    src_orders = f"source.{project_name}.ods.orders"

    nodes = {
        f"model.{project_name}.customers": model(
            unique_id=f"model.{project_name}.customers",
            name="customers",
            fqn=[project_name, "dwd", "customers"],
            depends_on=[src_customers],
        ),
        f"model.{project_name}.orders": model(
            unique_id=f"model.{project_name}.orders",
            name="orders",
            fqn=[project_name, "dwd", "orders"],
            depends_on=[src_orders, f"model.{project_name}.customers"],
        ),
        f"model.{project_name}.dim_customer": model(
            unique_id=f"model.{project_name}.dim_customer",
            name="dim_customer",
            fqn=[project_name, "dws", "dim_customer"],
            depends_on=[f"model.{project_name}.customers"],
            tags=["dim"],
        ),
        f"model.{project_name}.fact_orders_daily": model(
            unique_id=f"model.{project_name}.fact_orders_daily",
            name="fact_orders_daily",
            fqn=[project_name, "dws", "fact_orders_daily"],
            depends_on=[f"model.{project_name}.orders"],
            tags=["daily"],
        ),
        f"model.{project_name}.fact_orders_hourly": model(
            unique_id=f"model.{project_name}.fact_orders_hourly",
            name="fact_orders_hourly",
            fqn=[project_name, "dws", "fact_orders_hourly"],
            depends_on=[f"model.{project_name}.orders"],
        ),
        f"model.{project_name}.fact_customer_orders_daily": model(
            unique_id=f"model.{project_name}.fact_customer_orders_daily",
            name="fact_customer_orders_daily",
            fqn=[project_name, "dws", "fact_customer_orders_daily"],
            depends_on=[f"model.{project_name}.orders", f"model.{project_name}.customers"],
            tags=["daily"],
        ),
    }

    sources = {
        src_customers: source(src_customers, "ods", "customers"),
        src_orders: source(src_orders, "ods", "orders"),
    }

    child_map = {unique_id: [] for unique_id in {**nodes, **sources}.keys()}
    for unique_id, info in nodes.items():
        for upstream in info.get("depends_on", {}).get("nodes", []):
            child_map.setdefault(upstream, []).append(unique_id)

    return {
        "metadata": {
            "project_name": project_name,
            "adapter_type": "starrocks",
            "dbt_version": "1.11.7",
        },
        "nodes": nodes,
        "sources": sources,
        "metrics": {},
        "exposures": {},
        "semantic_models": {},
        "saved_queries": {},
        "selectors": {},
        "unit_tests": {},
        "functions": {},
        "child_map": child_map,
    }
dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    target=dbt_target,
    packaged_project_dir=dbt_project_dir,
)

parse_on_load_disabled = os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "1").strip().lower() in {
    "0",
    "false",
    "no",
}
manifest = _stub_manifest() if (parse_on_load_disabled and (not dbt_project.manifest_path.exists())) else dbt_project.manifest_path

prepare_if_dev = os.getenv("LUBAN_DBT_PREPARE_IF_DEV", "1").strip().lower() in {"1", "true", "yes"}
if prepare_if_dev and (manifest is dbt_project.manifest_path) and (not dbt_project.manifest_path.exists()):
    prep = DbtCliResource(
        project_dir=str(dbt_project_dir),
        profiles_dir=str(dbt_profiles_dir),
        target=dbt_target,
    )
    prep.cli(["deps", "--quiet"], target_path=str(dbt_project.target_path)).wait()
    prep.cli(["parse", "--quiet"], target_path=str(dbt_project.target_path)).wait()


@dbt_assets(
    manifest=manifest,
    dagster_dbt_translator=LubanDagsterDbtTranslator(daily_partitions_def=daily_partitions_def),
)
def dbt_assets(context, dbt: DbtCliResource):
    dbt_vars = _get_dbt_vars_for_context(context)
    dbt_args = ["build"]
    if dbt_vars:
        dbt_args += ["--vars", json.dumps(dbt_vars)]
    yield from dbt.cli(dbt_args, context=context).stream()
