from __future__ import annotations


def build_stub_manifest(*, project_name: str, adapter_type: str) -> dict:
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
            "adapter_type": adapter_type,
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
