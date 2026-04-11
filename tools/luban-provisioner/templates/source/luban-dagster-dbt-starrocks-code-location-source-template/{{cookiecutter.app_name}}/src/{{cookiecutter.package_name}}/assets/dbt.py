import json
import os

from dagster import DailyPartitionsDefinition
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

from ..resources.dbt import get_dbt_project_dir
from .automation_config import DYNAMIC_PARTITION_PIPELINES
from .lib.dbt_prepare import prepare_manifest_if_missing
from .lib.dbt_translator import LubanDagsterDbtTranslator
from .lib.partition_vars import _get_dbt_vars_for_context


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

dagster_dbt_translator = LubanDagsterDbtTranslator(daily_partitions_def=daily_partitions_def)


def _sanitize_name(value: str) -> str:
    return "".join([c if (c.isalnum() or c == "_") else "_" for c in value])


def _build_dbt_assets_def(*, name: str, select: str, exclude: str | None = None):
    @dbt_assets(
        manifest=dbt_project.manifest_path,
        dagster_dbt_translator=dagster_dbt_translator,
        select=select,
        exclude=exclude,
        name=name,
    )
    def _assets(context, dbt: DbtCliResource):
        dbt_vars = _get_dbt_vars_for_context(context)
        dbt_args = ["build"]
        if dbt_vars:
            dbt_args += ["--vars", json.dumps(dbt_vars)]
        yield from dbt.cli(dbt_args, context=context).stream()

    return _assets


dynamic_pipeline_tags = sorted(
    {
        spec["dbt_tag"]
        for spec in (DYNAMIC_PARTITION_PIPELINES or [])
        if isinstance(spec.get("dbt_tag"), str) and str(spec["dbt_tag"]).startswith("dynamic__")
    }
)

excluded_tags = ["tag:daily"] + [f"tag:{t}" for t in dynamic_pipeline_tags]
exclude_unpartitioned = " ".join([t for t in excluded_tags if t])

assets_defs = [
    _build_dbt_assets_def(name="dbt_assets__daily", select="tag:daily"),
]

for tag in dynamic_pipeline_tags:
    assets_defs.append(
        _build_dbt_assets_def(
            name=_sanitize_name(f"dbt_assets__{tag}"),
            select=f"tag:{tag}",
        )
    )

assets_defs.append(
    _build_dbt_assets_def(
        name="dbt_assets__unpartitioned",
        select="fqn:*",
        exclude=exclude_unpartitioned,
    )
)


dbt_assets = assets_defs
