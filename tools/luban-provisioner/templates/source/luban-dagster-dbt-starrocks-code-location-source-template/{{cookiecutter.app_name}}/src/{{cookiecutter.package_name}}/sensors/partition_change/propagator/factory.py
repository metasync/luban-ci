from __future__ import annotations

import dagster as dg


def build_partition_propagation_sensors(*, specs: list[dict], jobs_by_name: dict) -> list[dg.SensorDefinition]:
    sensors: list[dg.SensorDefinition] = []
    duplicated = _get_duplicated_spec_names(specs)
    if duplicated:
        raise ValueError(f"Duplicate partition propagation sensor names: {sorted(duplicated)}")

    def _make_sensor(spec: dict) -> dg.SensorDefinition:
        name = spec["name"]
        upstream_dbt_model = spec["upstream_dbt_model"]
        job_name = spec["job_name"]

        enabled = bool(spec.get("enabled", False))
        default_status = dg.DefaultSensorStatus.RUNNING if enabled else dg.DefaultSensorStatus.STOPPED
        minimum_interval_seconds = int(spec.get("minimum_interval_seconds", 30))

        job = jobs_by_name[job_name]
        upstream_asset_key = dg.AssetKey(["dbt", upstream_dbt_model])

        @dg.asset_sensor(
            name=name,
            asset_key=upstream_asset_key,
            job=job,
            default_status=default_status,
            minimum_interval_seconds=minimum_interval_seconds,
        )
        def _sensor(context: dg.SensorEvaluationContext, asset_event):
            dagster_event = getattr(asset_event, "dagster_event", None)
            if dagster_event is None:
                yield dg.SkipReason("Missing dagster_event")
                return

            partition_key = (dagster_event.logging_tags or {}).get("dagster/partition")
            if not partition_key:
                yield dg.SkipReason("Upstream event had no partition tag")
                return

            run_id = getattr(dagster_event, "run_id", "")
            run_key = f"{name}:{partition_key}:{run_id}"

            yield dg.RunRequest(partition_key=partition_key, run_key=run_key)

        return _sensor

    sensors += [_make_sensor(spec) for spec in specs]

    return sensors


def _get_duplicated_spec_names(specs: list[dict]) -> set[str]:
    duplicated: set[str] = set()
    seen: set[str] = set()
    for spec in specs:
        name = spec.get("name")
        if not name:
            continue
        if name in seen:
            duplicated.add(name)
        else:
            seen.add(name)
    return duplicated
