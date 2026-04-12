from .dbt.schedules import dbt_schedules
from .sources.schedules import observe_sources_schedule

schedules = [
    *dbt_schedules,
    observe_sources_schedule,
]
