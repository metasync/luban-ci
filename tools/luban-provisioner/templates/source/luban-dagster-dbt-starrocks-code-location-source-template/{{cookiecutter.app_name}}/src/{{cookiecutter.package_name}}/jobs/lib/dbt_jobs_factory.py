import json

import dagster as dg
from dagster import AssetKey, AssetSelection, define_asset_job


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
    op_name = _sanitized_name(f"run_{job_name}")

    @dg.op(name=op_name, required_resource_keys={"dbt"})
    def _run(context):
        args = [command, "--select", select]
        if vars_dict:
            args += ["--vars", json.dumps(vars_dict)]
        yield from context.resources.dbt.cli(args, context=context).stream()

    @dg.job(name=job_name)
    def _job():
        _run()

    return _job


def build_dbt_asset_jobs(job_specs):
    job_names = [spec.get("name") for spec in job_specs]
    duplicated = {name for name in job_names if name and job_names.count(name) > 1}
    if duplicated:
        raise ValueError(f"Duplicate dbt job names: {sorted(duplicated)}")

    jobs_by_name = {}
    for job_spec in job_specs:
        job_type = job_spec.get("type", "asset")
        name = job_spec["name"]
        if job_type == "asset":
            selection = _build_selection(job_spec["selection"])
            jobs_by_name[name] = define_asset_job(name=name, selection=selection)
        elif job_type == "dbt_cli":
            jobs_by_name[name] = _build_dbt_cli_job(job_spec)
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

    return jobs_by_name

