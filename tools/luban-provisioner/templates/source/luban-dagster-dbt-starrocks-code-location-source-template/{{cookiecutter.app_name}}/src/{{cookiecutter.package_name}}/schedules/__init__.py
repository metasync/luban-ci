from .dbt import dbt_schedules
from .observations import observe_sources_schedule

schedules = [
    *dbt_schedules,
    observe_sources_schedule,
]

