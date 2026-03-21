from .dbt import dbt_jobs
from .observations import observe_sources_job

jobs = [
    *dbt_jobs,
    observe_sources_job,
]

