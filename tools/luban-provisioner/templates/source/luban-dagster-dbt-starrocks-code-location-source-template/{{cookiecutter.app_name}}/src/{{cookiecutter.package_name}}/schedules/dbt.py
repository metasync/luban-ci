from dagster import ScheduleDefinition

from ..jobs.dbt import dbt_jobs_by_name
from .dbt_config import DBT_SCHEDULE_SPECS


schedule_names = [spec.get("name") for spec in DBT_SCHEDULE_SPECS]
duplicated = {name for name in schedule_names if name and schedule_names.count(name) > 1}
if duplicated:
    raise ValueError(f"Duplicate dbt schedule names: {sorted(duplicated)}")


dbt_schedules_by_name = {
    spec["name"]: ScheduleDefinition(
        name=spec["name"],
        cron_schedule=spec["cron_schedule"],
        job=dbt_jobs_by_name[spec["job_name"]],
    )
    for spec in DBT_SCHEDULE_SPECS
    if spec.get("enabled", True)
}

dbt_schedules = list(dbt_schedules_by_name.values())

