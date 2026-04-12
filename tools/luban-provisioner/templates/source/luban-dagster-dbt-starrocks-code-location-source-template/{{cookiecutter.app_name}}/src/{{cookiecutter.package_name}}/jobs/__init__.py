from .dbt.jobs import dbt_jobs
from .sources.jobs import observe_sources_job

jobs = [
    *dbt_jobs,
    observe_sources_job,
]
