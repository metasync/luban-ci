import json
import os
import time

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets
from dagster_dbt.errors import DagsterDbtCliRuntimeError

from ...resources.dbt import get_dbt_project_dir
from ..sources.automation import load_automation_observable_sources
from .prepare import prepare_manifest_if_missing
from .translator import LubanDagsterDbtTranslator
from .vars import _get_dbt_vars_for_context


daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-03-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

dbt_project_dir = get_dbt_project_dir()
dbt_target = os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}")
dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    target=dbt_target,
    packaged_project_dir=dbt_project_dir,
)

prepare_manifest_if_missing()
automation_observable_tables = {
    spec["table"] for spec in load_automation_observable_sources() if spec.get("table")
}


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=LubanDagsterDbtTranslator(
        daily_partitions_def=daily_partitions_def,
        automation_observable_tables=automation_observable_tables,
    ),
)
def dbt_assets(context, dbt: DbtCliResource):
    dbt_vars = _get_dbt_vars_for_context(context)
    dbt_args = ["build"]
    if dbt_vars:
        dbt_args += ["--vars", json.dumps(dbt_vars)]

    try:
        yield from dbt.cli(dbt_args, context=context).stream()
    except DagsterDbtCliRuntimeError as e:
        message = str(e)
        if "already exists" not in message:
            raise
        time.sleep(2)
        yield from dbt.cli(dbt_args, context=context).stream()
