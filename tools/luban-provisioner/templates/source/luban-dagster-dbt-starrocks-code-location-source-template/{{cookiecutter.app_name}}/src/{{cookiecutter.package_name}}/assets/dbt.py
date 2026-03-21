import os

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir
from .lib.dbt_translator import LubanDagsterDbtTranslator

daily_partitions_start_date = os.getenv("DAGSTER_DAILY_PARTITIONS_START_DATE", "2026-01-01")
daily_partitions_def = DailyPartitionsDefinition(start_date=daily_partitions_start_date)

dbt_project_dir = get_dbt_project_dir()
dbt_project = DbtProject(
    project_dir=dbt_project_dir,
    target=os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}"),
    packaged_project_dir=dbt_project_dir,
)

prepare_if_dev = os.getenv("LUBAN_DBT_PREPARE_IF_DEV", "1").strip().lower() in {"1", "true", "yes"}
if prepare_if_dev:
    dbt_project.prepare_if_dev()


@dbt_assets(
    manifest=dbt_project.manifest_path,
    dagster_dbt_translator=LubanDagsterDbtTranslator(daily_partitions_def=daily_partitions_def),
)
def dbt_assets(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()

