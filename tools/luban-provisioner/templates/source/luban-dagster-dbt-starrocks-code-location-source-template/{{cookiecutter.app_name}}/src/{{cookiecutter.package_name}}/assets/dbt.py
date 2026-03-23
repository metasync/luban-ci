import os
import json

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir, get_dbt_profiles_dir
from .lib.partition_vars import _get_dbt_vars_for_context
from .lib.dbt_translator import LubanDagsterDbtTranslator
from .lib.stub_manifest import build_stub_manifest

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

parse_on_load_disabled = os.getenv("DAGSTER_DBT_PARSE_PROJECT_ON_LOAD", "1").strip().lower() in {
    "0",
    "false",
    "no",
}
manifest = (
    build_stub_manifest(project_name="{{cookiecutter.package_name}}_dbt", adapter_type="starrocks")
    if (parse_on_load_disabled and (not dbt_project.manifest_path.exists()))
    else dbt_project.manifest_path
)

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
