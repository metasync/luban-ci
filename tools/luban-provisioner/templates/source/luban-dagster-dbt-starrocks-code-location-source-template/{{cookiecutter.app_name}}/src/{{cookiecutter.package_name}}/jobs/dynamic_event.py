from __future__ import annotations

import json
import os

import dagster as dg
from dagster_dbt.utils import ASSET_RESOURCE_TYPES, select_unique_ids

from ..assets.automation_config import DYNAMIC_PARTITION_PIPELINES
from ..assets.lib.dbt_prepare import prepare_manifest_if_missing
from ..assets.lib.dbt_translator import LubanDagsterDbtTranslator
from ..resources.dbt import get_dbt_project_dir


def _load_manifest() -> dict:
    manifest_path = get_dbt_project_dir() / "target" / "manifest.json"
    if not manifest_path.exists():
        prepare_manifest_if_missing()
    if not manifest_path.exists():
        raise FileNotFoundError(f"dbt manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text())


def _asset_selection_for_dbt_tag(*, dbt_tag: str) -> dg.AssetSelection:
    manifest = _load_manifest()

    unique_ids = select_unique_ids(
        select=f"tag:{dbt_tag}",
        exclude="",
        selector="",
        project=None,
        manifest_json=manifest,
    )

    daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-03-01")
    translator = LubanDagsterDbtTranslator(
        daily_partitions_def=dg.DailyPartitionsDefinition(start_date=daily_partitions_start_date)
    )

    keys: list[dg.AssetKey] = []
    nodes = manifest.get("nodes") or {}
    sources = manifest.get("sources") or {}

    for unique_id in sorted(unique_ids):
        props = nodes.get(unique_id) or sources.get(unique_id)
        if not props:
            continue

        resource_type = props.get("resource_type")
        if resource_type == "model" and (props.get("config") or {}).get("materialized") == "ephemeral":
            continue

        if resource_type not in set(ASSET_RESOURCE_TYPES) | {"source"}:
            continue

        keys.append(translator.get_asset_key(props))

    if not keys:
        raise ValueError(f"No dbt assets matched selection tag:{dbt_tag}.")

    return dg.AssetSelection.keys(*keys)


def build_dynamic_partition_job(*, dbt_tag: str, partitions_def_name: str, job_name: str):
    partitions_def = dg.DynamicPartitionsDefinition(name=partitions_def_name)
    selection = _asset_selection_for_dbt_tag(dbt_tag=dbt_tag)
    return dg.define_asset_job(
        name=job_name,
        selection=selection,
        partitions_def=partitions_def,
    )


dynamic_partition_jobs_by_name = {}
for _spec in DYNAMIC_PARTITION_PIPELINES:
    _job = build_dynamic_partition_job(
        dbt_tag=_spec["dbt_tag"],
        partitions_def_name=_spec["partitions_def_name"],
        job_name=_spec["job_name"],
    )
    dynamic_partition_jobs_by_name[_job.name] = _job


dynamic_partition_jobs = list(dynamic_partition_jobs_by_name.values())
