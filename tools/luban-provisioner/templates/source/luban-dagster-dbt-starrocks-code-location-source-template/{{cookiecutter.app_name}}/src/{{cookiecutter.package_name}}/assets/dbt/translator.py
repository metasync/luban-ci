from __future__ import annotations

import os
from typing import Any, Mapping, Optional

import dagster as dg
from dagster_dbt import DagsterDbtTranslator


class LubanDagsterDbtTranslator(DagsterDbtTranslator):
    def __init__(
        self,
        daily_partitions_def: dg.PartitionsDefinition,
        automation_observable_tables: set[str],
    ):
        super().__init__()
        self.daily_partitions_def = daily_partitions_def
        self.automation_observable_tables = automation_observable_tables
        self.propagator_mode = os.getenv("LUBAN_PARTITION_CHANGE_PROPAGATOR_MODE", "sensor").strip().lower()

    def get_automation_condition(self, dbt_resource_props):
        resource_type = dbt_resource_props.get("resource_type")
        if resource_type != "model":
            return None

        fqn = dbt_resource_props.get("fqn", [])
        name = dbt_resource_props.get("name")
        tags = set(dbt_resource_props.get("tags", []))

        automation_tables = self.automation_observable_tables

        if "dwd" in fqn and name in automation_tables:
            return dg.AutomationCondition.eager()

        if self._propagator_mode_is_eager() and "dws" in fqn and "daily" in tags:
            return dg.AutomationCondition.eager()

        if "dws" in fqn and "dim" in tags:
            return dg.AutomationCondition.eager()

        return None

    def _propagator_mode_is_eager(self) -> bool:
        return self.propagator_mode == "eager"

    def get_asset_key(self, dbt_resource_props: Mapping[str, Any]) -> dg.AssetKey:
        resource_type = dbt_resource_props.get("resource_type")
        if resource_type == "source":
            base_key = dg.AssetKey([dbt_resource_props["source_name"], dbt_resource_props["name"]])
        else:
            base_key = dg.AssetKey([dbt_resource_props["name"]])

        return base_key.with_prefix("dbt")

    def get_group_name(self, dbt_resource_props: Mapping[str, Any]) -> Optional[str]:
        fqn = dbt_resource_props.get("fqn", [])
        if "dwd" in fqn:
            return "dwd"
        if "dws" in fqn:
            return "dws"
        return None

    def get_partitions_def(self, dbt_resource_props: Mapping[str, Any]) -> Optional[dg.PartitionsDefinition]:
        tags = set(dbt_resource_props.get("tags", []))

        if "daily" in tags:
            return self.daily_partitions_def

        return None

