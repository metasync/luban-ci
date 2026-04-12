import os

from dagster import DefaultScheduleStatus, ScheduleDefinition

from ...jobs.sources.jobs import observe_sources_job


observe_sources_schedule = ScheduleDefinition(
    name="observe_sources_schedule",
    cron_schedule=os.getenv("LUBAN_OBSERVE_SOURCES_CRON", "*/5 * * * *"),
    job=observe_sources_job,
    default_status=DefaultScheduleStatus.RUNNING,
)

