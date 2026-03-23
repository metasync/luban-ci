from __future__ import annotations

import os
from pathlib import Path

from dagster_dbt import DbtCliResource

from ...resources.dbt import get_dbt_profiles_dir, get_dbt_project_dir


def prepare_manifest_if_missing(*, target: str | None = None) -> None:
    enabled = os.getenv("LUBAN_DBT_PREPARE_ON_LOAD", "1").strip().lower() in {"1", "true", "yes"}
    if not enabled:
        return

    project_dir = get_dbt_project_dir()
    profiles_dir = get_dbt_profiles_dir()
    target = target or os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}")

    manifest_path = project_dir / "target" / "manifest.json"
    if manifest_path.exists():
        return

    target_path = project_dir / "target"
    prep = DbtCliResource(
        project_dir=str(project_dir),
        profiles_dir=str(profiles_dir),
        target=target,
    )
    prep.cli(["deps", "--quiet"], target_path=target_path).wait()
    prep.cli(["parse", "--quiet"], target_path=target_path).wait()
