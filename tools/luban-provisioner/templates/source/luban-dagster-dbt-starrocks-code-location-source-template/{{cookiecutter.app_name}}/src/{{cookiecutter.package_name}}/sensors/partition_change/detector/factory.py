from __future__ import annotations

from datetime import datetime, timedelta, timezone

import dagster as dg

from ....assets.dbt.prepare import prepare_manifest_if_missing
from ....jobs.dbt.jobs import dbt_jobs_by_name
from .dbt_manifest import get_model_node_by_name, load_manifest
from .sparse_lookback import detect_changed_partition_dates, parse_sparse_lookback_meta


def _parse_cursor(cursor: str | None) -> datetime | None:
    if not cursor:
        return None
    try:
        return datetime.fromisoformat(cursor)
    except Exception:
        return None


def build_dbt_partition_change_sensors(*, specs: list[dict]) -> list[dg.SensorDefinition]:
    duplicated = set()
    seen = set()
    for spec in specs:
        name = spec.get("name")
        if not name:
            continue
        if name in seen:
            duplicated.add(name)
        else:
            seen.add(name)
    if duplicated:
        raise ValueError(f"Duplicate partition change sensor names: {sorted(duplicated)}")

    def _make_sensor(spec: dict) -> dg.SensorDefinition:
        enabled = bool(spec.get("enabled", True))
        default_status = dg.DefaultSensorStatus.RUNNING if enabled else dg.DefaultSensorStatus.STOPPED

        partition_type = spec.get("partition_type", "daily")
        if partition_type != "daily":
            raise ValueError(f"Unsupported partition_type: {partition_type}")

        sensor_name = spec["name"]
        job_name = spec["job_name"]
        detector_model = spec["detector_model"]
        job = dbt_jobs_by_name[job_name]

        lookback_days = int(spec.get("lookback_days", 0))
        offset_days = int(spec.get("offset_days", 0))
        minimum_interval_seconds = int(spec.get("minimum_interval_seconds", 60))

        @dg.sensor(
            name=sensor_name,
            job=job,
            default_status=default_status,
            minimum_interval_seconds=minimum_interval_seconds,
            required_resource_keys={"starrocks"},
        )
        def _sensor(context: dg.SensorEvaluationContext):
            prepare_manifest_if_missing()
            manifest = load_manifest()
            node = get_model_node_by_name(manifest, detector_model)
            luban_meta = node.meta.get("luban")
            if not isinstance(luban_meta, dict):
                luban_meta = {}
            pc_meta = luban_meta.get("partition_change")
            if not isinstance(pc_meta, dict):
                pc_meta = {}
            detector_meta = pc_meta.get("detector")
            if not isinstance(detector_meta, dict):
                detector_meta = {}
            if not detector_meta:
                raise ValueError(
                    f"Model '{detector_model}' is configured as a partition change detector but lacks meta.luban.partition_change.detector"
                )
            sparse_meta = parse_sparse_lookback_meta(meta=detector_meta, manifest=manifest)

            now = datetime.now(timezone.utc)
            anchor_day = (now - timedelta(days=offset_days)).date()
            window_start = anchor_day - timedelta(days=lookback_days)
            window_end = anchor_day

            cursor_ts = _parse_cursor(context.cursor)
            if cursor_ts is None:
                cursor_ts = now - timedelta(days=lookback_days + offset_days + 1)

            changed_dates = detect_changed_partition_dates(
                starrocks=context.resources.starrocks,
                meta=sparse_meta,
                window_start=window_start,
                window_end=window_end,
                since_ts=cursor_ts,
            )

            partition_keys = sorted([d.isoformat() for d in changed_dates if window_start <= d <= window_end])
            for partition_key in partition_keys:
                run_key = f"{sensor_name}:{partition_key}:{now.strftime('%Y%m%dT%H%M%S')}"
                yield dg.RunRequest(
                    partition_key=partition_key,
                    run_key=run_key,
                    tags={
                        "luban/detector_model": detector_model,
                        "luban/detect_relation": sparse_meta.detect_relation,
                    },
                )

            context.update_cursor(now.isoformat())

        return _sensor

    return [_make_sensor(spec) for spec in specs]
