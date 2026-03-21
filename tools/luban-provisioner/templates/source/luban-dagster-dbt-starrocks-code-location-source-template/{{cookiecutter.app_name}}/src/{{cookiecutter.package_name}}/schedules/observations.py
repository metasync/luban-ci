from dagster import ScheduleDefinition

from ..jobs.observations import observe_sources_job


observe_sources_schedule = ScheduleDefinition(
    name="observe_sources_schedule",
    cron_schedule="* * * * *",
    job=observe_sources_job,
)

