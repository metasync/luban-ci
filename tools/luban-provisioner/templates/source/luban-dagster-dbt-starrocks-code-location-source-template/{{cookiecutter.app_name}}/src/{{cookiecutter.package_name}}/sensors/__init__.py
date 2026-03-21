import dagster as dg


automation_condition_sensor = dg.AutomationConditionSensorDefinition(
    "default_automation_condition_sensor",
    target=dg.AssetSelection.all(),
    default_status=dg.DefaultSensorStatus.RUNNING,
)


sensors = [automation_condition_sensor]

