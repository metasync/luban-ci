import os
from pathlib import Path

from dagster_dbt import DbtCliResource


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def get_dbt_project_dir() -> Path:
    project_dir = os.getenv("DBT_PROJECT_DIR")
    if not project_dir:
        return get_repo_root() / "dbt_project"

    path = Path(project_dir).expanduser()
    if path.is_absolute():
        return path

    return (get_repo_root() / path).resolve()


def get_dbt_profiles_dir() -> Path:
    profiles_dir = os.getenv("DBT_PROFILES_DIR")
    if not profiles_dir:
        return get_dbt_project_dir()

    path = Path(profiles_dir).expanduser()
    if path.is_absolute():
        return path

    return (get_repo_root() / path).resolve()


def make_dbt_resource() -> DbtCliResource:
    target = os.getenv("DBT_TARGET", "{{ cookiecutter.default_env }}")

    return DbtCliResource(
        project_dir=str(get_dbt_project_dir()),
        profiles_dir=str(get_dbt_profiles_dir()),
        target=target,
    )

