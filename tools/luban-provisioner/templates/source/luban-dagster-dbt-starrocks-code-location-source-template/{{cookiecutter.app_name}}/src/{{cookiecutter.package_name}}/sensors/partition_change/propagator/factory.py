from __future__ import annotations

import os
import time

import dagster as dg
from dagster._core.event_api import EventRecordsFilter


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

        catchup_days = int(os.getenv("LUBAN_PARTITION_CHANGE_PROPAGATOR_CATCHUP_DAYS", "0"))
        if catchup_days < 0:
            raise ValueError("LUBAN_PARTITION_CHANGE_PROPAGATOR_CATCHUP_DAYS must be >= 0")

        @dg.sensor(
            name=name,
            job=job,
            default_status=default_status,
            minimum_interval_seconds=minimum_interval_seconds,
        )
        def _sensor(context: dg.SensorEvaluationContext):
            cursor = (context.cursor or "").strip()
            now = time.time()

            after_cursor = None
            after_timestamp = None

            if cursor:
                try:
                    after_cursor = int(cursor)
                except Exception:
                    context.update_cursor("")
                    cursor = ""
            elif catchup_days > 0:
                after_timestamp = now - (catchup_days * 86400)
            else:
                latest = context.instance.get_event_records(
                    EventRecordsFilter(
                        event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
                        asset_key=upstream_asset_key,
                    ),
                    limit=1,
                    ascending=False,
                )
                if latest:
                    context.update_cursor(str(latest[0].storage_id))
                yield dg.SkipReason(
                    "Initialized propagation cursor (set LUBAN_PARTITION_CHANGE_PROPAGATOR_CATCHUP_DAYS to backfill)"
                )
                return

            records = context.instance.get_event_records(
                EventRecordsFilter(
                    event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
                    asset_key=upstream_asset_key,
                    after_cursor=after_cursor,
                    after_timestamp=after_timestamp,
                ),
                limit=1000,
                ascending=True,
            )

            latest_by_partition: dict[str, object] = {}
            for r in records:
                entry = r.event_log_entry
                mat = getattr(entry, "asset_materialization", None)
                partition_key = getattr(mat, "partition", None)
                if not partition_key:
                    continue
                latest_by_partition[str(partition_key)] = r

            if not latest_by_partition:
                yield dg.SkipReason(f"No new materialization events found for asset key {upstream_asset_key}")
                return

            max_storage_id = max([r.storage_id for r in latest_by_partition.values()])
            for partition_key, r in sorted(latest_by_partition.items()):
                run_key = f"{name}:{partition_key}:{r.run_id}:{r.storage_id}"
                yield dg.RunRequest(partition_key=partition_key, run_key=run_key)

            context.update_cursor(str(max_storage_id))

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
