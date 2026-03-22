from ..jobs.dbt import dbt_jobs_by_name
from .dbt_config import DBT_SCHEDULE_SPECS
from .lib.dbt_schedules_factory import build_dbt_schedules


dbt_schedules = build_dbt_schedules(DBT_SCHEDULE_SPECS, dbt_jobs_by_name)
