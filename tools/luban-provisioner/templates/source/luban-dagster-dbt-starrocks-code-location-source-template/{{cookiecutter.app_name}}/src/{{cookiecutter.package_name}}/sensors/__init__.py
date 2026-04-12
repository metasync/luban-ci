import os

import dagster as dg

from ..jobs.dbt.jobs import dbt_jobs_by_name
from .dbt_config import PARTITION_CHANGE_DETECTION_SPECS, PARTITION_CHANGE_PROPAGATION_SPECS
from .partition_change.auto_config import (
    build_auto_partition_change_detection_specs,
    build_auto_partition_change_propagation_specs,
)
from .partition_change.detector.factory import build_dbt_partition_change_sensors
from .partition_change.propagator.factory import build_partition_propagation_sensors


automation_condition_sensor = dg.AutomationConditionSensorDefinition(
    "default_automation_condition_sensor",
    target=dg.AssetSelection.all(),
    default_status=dg.DefaultSensorStatus.RUNNING,
)


sensors = [automation_condition_sensor]

sensors += build_dbt_partition_change_sensors(
    specs=build_auto_partition_change_detection_specs() + PARTITION_CHANGE_DETECTION_SPECS,
)

propagator_mode = os.getenv("LUBAN_PARTITION_CHANGE_PROPAGATOR_MODE", "sensor").strip().lower()
if propagator_mode != "eager":
    sensors += build_partition_propagation_sensors(
        specs=build_auto_partition_change_propagation_specs() + PARTITION_CHANGE_PROPAGATION_SPECS,
        jobs_by_name=dbt_jobs_by_name,
    )
