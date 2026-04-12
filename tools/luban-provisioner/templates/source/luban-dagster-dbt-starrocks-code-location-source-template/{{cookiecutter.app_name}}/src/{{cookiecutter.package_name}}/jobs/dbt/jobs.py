from ..dbt_config import DBT_JOB_SPECS
from .auto_config import build_auto_dbt_job_specs
from .factory import build_dbt_asset_jobs


dbt_jobs_by_name = build_dbt_asset_jobs(build_auto_dbt_job_specs() + DBT_JOB_SPECS)
dbt_jobs = list(dbt_jobs_by_name.values())
