from .dbt_config import DBT_JOB_SPECS
from .lib.dbt_jobs_factory import build_dbt_asset_jobs


dbt_jobs_by_name = build_dbt_asset_jobs(DBT_JOB_SPECS)
dbt_jobs = list(dbt_jobs_by_name.values())

