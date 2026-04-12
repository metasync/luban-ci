from ...jobs.dbt.jobs import dbt_jobs_by_name
from ..dbt_config import DBT_SCHEDULE_SPECS
from .auto_config import build_auto_dbt_schedule_specs
from .factory import build_dbt_schedules


dbt_schedules = build_dbt_schedules(build_auto_dbt_schedule_specs() + DBT_SCHEDULE_SPECS, dbt_jobs_by_name)
