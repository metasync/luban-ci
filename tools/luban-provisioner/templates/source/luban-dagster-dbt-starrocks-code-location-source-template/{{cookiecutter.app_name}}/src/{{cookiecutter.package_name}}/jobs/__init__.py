from .dbt import dbt_jobs
from .dynamic_event import dynamic_partition_jobs
from .observations import observe_sources_job

jobs = [
    *dbt_jobs,
    *dynamic_partition_jobs,
    observe_sources_job,
]

