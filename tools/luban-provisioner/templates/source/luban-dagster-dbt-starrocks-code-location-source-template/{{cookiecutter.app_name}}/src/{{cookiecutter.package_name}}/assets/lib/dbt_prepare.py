from __future__ import annotations

from pathlib import Path

from dagster_dbt import DbtCliResource


def prepare_manifest_if_missing(
    *,
    enabled: bool,
    project_dir: Path,
    profiles_dir: Path,
    target: str,
    target_path: Path,
    manifest_path: Path,
) -> None:
    if (not enabled) or manifest_path.exists():
        return

    prep = DbtCliResource(
        project_dir=str(project_dir),
        profiles_dir=str(profiles_dir),
        target=target,
    )
    prep.cli(["deps", "--quiet"], target_path=target_path).wait()
    prep.cli(["parse", "--quiet"], target_path=target_path).wait()
