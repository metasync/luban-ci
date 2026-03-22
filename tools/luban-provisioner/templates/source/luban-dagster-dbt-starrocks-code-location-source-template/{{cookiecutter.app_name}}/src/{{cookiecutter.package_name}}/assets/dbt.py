import os
import json

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir
from .lib.partition_vars import _get_dbt_vars_for_context
from .lib.dbt_translator import LubanDagsterDbtTranslator

daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-01-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

dbt_project_dir = get_dbt_project_dir()
dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    target=os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}"),
    packaged_project_dir=dbt_project_dir,
)

parse_on_load = os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "1").strip().lower() not in {"0", "false", "no"}
prepare_if_dev = os.getenv("LUBAN_DBT_PREPARE_IF_DEV", "0").strip().lower() in {"1", "true", "yes"}
if prepare_if_dev and parse_on_load:
    dbt_project.prepare_if_dev()


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=LubanDagsterDbtTranslator(daily_partitions_def=daily_partitions_def),
)
def dbt_assets(context, dbt: DbtCliResource):
    dbt_vars = _get_dbt_vars_for_context(context)
    dbt_args = ["build"]
    if dbt_vars:
        dbt_args += ["--vars", json.dumps(dbt_vars)]
    yield from dbt.cli(dbt_args, context=context).stream()
