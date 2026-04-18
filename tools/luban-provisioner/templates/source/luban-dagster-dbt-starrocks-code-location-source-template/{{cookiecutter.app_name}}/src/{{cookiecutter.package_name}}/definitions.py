import os
from pathlib import Path

from dbt_dagsterizer.api import build_definitions


REPO_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = REPO_ROOT / "dbt_project"

os.environ.setdefault("LUBAN_REPO_ROOT", str(REPO_ROOT))
os.environ.setdefault("DBT_PROJECT_DIR", str(DBT_PROJECT_DIR))
os.environ.setdefault("DBT_PROFILES_DIR", str(DBT_PROJECT_DIR))


defs = build_definitions(
    dbt_project_dir=DBT_PROJECT_DIR,
    dbt_profiles_dir=DBT_PROJECT_DIR,
    default_dbt_target="{{ cookiecutter.default_env }}",
)
