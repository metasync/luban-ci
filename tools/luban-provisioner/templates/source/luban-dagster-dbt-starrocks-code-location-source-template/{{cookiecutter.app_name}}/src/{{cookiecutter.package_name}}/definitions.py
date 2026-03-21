from dagster import Definitions

from .assets import assets
from .jobs import jobs
from .resources import resources
from .sensors import sensors
from .schedules import schedules


defs = Definitions(
    assets=assets,
    jobs=jobs,
    schedules=schedules,
    sensors=sensors,
    resources=resources,
)

