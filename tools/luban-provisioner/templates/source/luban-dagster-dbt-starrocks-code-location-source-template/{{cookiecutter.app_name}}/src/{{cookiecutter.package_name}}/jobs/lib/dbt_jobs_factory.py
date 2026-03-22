import json
import os

import dagster as dg
from dagster import AssetKey, AssetSelection, DailyPartitionsDefinition, HourlyPartitionsDefinition, define_asset_job

from ...assets.lib.partition_vars import _get_dbt_vars_for_context


daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-01-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

hourly_partitions_start_date = os.getenv("DAGSTER_HOURLY_PARTITIONS_START_DATE", "2026-01-01-00:00")
hourly_partitions_def = HourlyPartitionsDefinition(start_date=hourly_partitions_start_date)


def _get_partitions_def(partitions: str):
    if partitions == "daily":
        return daily_partitions_def
    if partitions == "hourly":
        return hourly_partitions_def
    raise ValueError(f"Unsupported partitions value: {partitions}")


def _build_selection(selection_spec):
    selection_type = selection_spec.get("type")
    if selection_type == "key_prefix":
        prefix = selection_spec["prefix"]
        return AssetSelection.key_prefixes(prefix)

    if selection_type == "asset_keys":
        keys = [AssetKey(path) for path in selection_spec["keys"]]
        selection = AssetSelection.keys(*keys)
        if selection_spec.get("upstream"):
            selection = selection.upstream()
        return selection

    raise ValueError(f"Unsupported selection type: {selection_type}")


def _sanitized_name(name: str) -> str:
    return "".join([c if (c.isalnum() or c == "_") else "_" for c in name])


def _build_dbt_cli_job(job_spec):
    job_name = job_spec["name"]
    command = job_spec.get("command", "build")
    select = job_spec["select"]
    vars_dict = job_spec.get("vars") or {}
    partitions = job_spec.get("partitions", "daily")
    partitions_def = _get_partitions_def(partitions)
    op_name = _sanitized_name(f"run_{job_name}")

    @dg.op(name=op_name, required_resource_keys={"dbt"})
    def _run(context):
        partition_vars = _get_dbt_vars_for_context(context) or {}
        combined_vars = {**partition_vars, **vars_dict}
        args = [command, "--select", select]
        if combined_vars:
            args += ["--vars", json.dumps(combined_vars)]
        yield from context.resources.dbt.cli(args, context=context).stream()

    @dg.job(name=job_name, partitions_def=partitions_def)
    def _job():
        _run()

    return _job


def build_dbt_asset_jobs(job_specs):
    duplicated = set()
    seen = set()
    for spec in job_specs:
        name = spec.get("name")
        if not name:
            continue
        if name in seen:
            duplicated.add(name)
        else:
            seen.add(name)
    if duplicated:
        raise ValueError(f"Duplicate dbt job names: {sorted(duplicated)}")

    jobs_by_name = {}
    for job_spec in job_specs:
        job_type = job_spec.get("type", "asset")
        name = job_spec["name"]
        if job_type == "asset":
            selection = _build_selection(job_spec["selection"])
            partitions = job_spec.get("partitions", "daily")
            partitions_def = _get_partitions_def(partitions)
            jobs_by_name[name] = define_asset_job(
                name=name,
                selection=selection,
                partitions_def=partitions_def,
            )
        elif job_type == "dbt_cli":
            jobs_by_name[name] = _build_dbt_cli_job(job_spec)
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

    return jobs_by_name
