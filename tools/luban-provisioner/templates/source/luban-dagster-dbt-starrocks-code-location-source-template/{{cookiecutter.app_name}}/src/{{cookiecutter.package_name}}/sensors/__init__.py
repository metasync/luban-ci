import dagster as dg

from ..assets.automation_config import DYNAMIC_PARTITION_PIPELINES
from ..jobs.dynamic_event import dynamic_partition_jobs_by_name
from .dynamic_partition_dispatcher import build_dynamic_partition_dispatcher_sensor


automation_condition_sensor = dg.AutomationConditionSensorDefinition(
    "default_automation_condition_sensor",
    target=dg.AssetSelection.all(),
    default_status=dg.DefaultSensorStatus.RUNNING,
)


dynamic_partition_sensors = []
for _spec in DYNAMIC_PARTITION_PIPELINES:
    _job_name = _spec["job_name"]
    _job = dynamic_partition_jobs_by_name[_job_name]
    dynamic_partition_sensors.append(
        build_dynamic_partition_dispatcher_sensor(
            sensor_name=_spec["sensor_name"],
            job=_job,
            partitions_def_name=_spec["partitions_def_name"],
            sources=_spec["sources"],
            dispatch_daily_utc_hour=_spec.get("dispatch_daily_utc_hour"),
            dispatch_slot_seconds=_spec.get("dispatch_slot_seconds"),
            max_keys_per_tick=_spec.get("max_keys_per_tick"),
            default_status=_spec.get("sensor_default_status", "RUNNING"),
        )
    )


sensors = [automation_condition_sensor, *dynamic_partition_sensors]
