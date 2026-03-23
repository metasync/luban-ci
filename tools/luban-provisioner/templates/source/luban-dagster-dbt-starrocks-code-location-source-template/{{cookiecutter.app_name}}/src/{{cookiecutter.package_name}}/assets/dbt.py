import os
import json

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir, get_dbt_profiles_dir
from .lib.dbt_prepare import prepare_manifest_if_missing
from .lib.partition_vars import _get_dbt_vars_for_context
from .lib.dbt_translator import LubanDagsterDbtTranslator

daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-01-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

dbt_project_dir = get_dbt_project_dir()
dbt_profiles_dir = get_dbt_profiles_dir()
dbt_target = os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}")
dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    target=dbt_target,
    packaged_project_dir=dbt_project_dir,
)

prepare_on_load = os.getenv("LUBAN_DBT_PREPARE_ON_LOAD", "1").strip().lower() in {"1", "true", "yes"}
prepare_manifest_if_missing(
    enabled=prepare_on_load,
    project_dir=dbt_project_dir,
    profiles_dir=dbt_profiles_dir,
    target=dbt_target,
    target_path=dbt_project.target_path,
    manifest_path=dbt_project.manifest_path,
)


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
