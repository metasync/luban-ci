from __future__ import annotations

from collections import defaultdict

from ...dbt.manifest import get_luban_meta, iter_models, load_manifest
from ...jobs.dbt.auto_config import extract_job_config
from .detector.presets import daily_partition_change
from .propagator.presets import partition_change_propagation


def build_auto_partition_change_detection_specs() -> list[dict]:
    manifest = load_manifest()
    models = iter_models(manifest)

    specs: list[dict] = []
    for m in models:
        pc = get_luban_meta(m.meta).get("partition_change")
        if not isinstance(pc, dict):
            continue
        detector = pc.get("detector")
        if not isinstance(detector, dict):
            continue

        enabled = bool(detector.get("enabled", False))
        if not enabled:
            continue

        job_name = detector.get("job_name")
        if not job_name:
            derived_job_name, _, _ = extract_job_config(m)
            if not derived_job_name:
                raise ValueError(
                    f"Partition-change detector on model '{m.name}' could not derive job_name; add tag 'asset_job', tag 'job:<name>', or meta.luban.job"
                )
            job_name = derived_job_name

        lookback_days = int(detector.get("lookback_days", 7))
        offset_days = int(detector.get("offset_days", 1))
        minimum_interval_seconds = int(detector.get("minimum_interval_seconds", 60))
        sensor_name = detector.get("name") or f"{m.name}_partition_change_sensor"

        specs.append(
            daily_partition_change(
                name=str(sensor_name),
                job_name=str(job_name),
                detector_model=m.name,
                lookback_days=lookback_days,
                offset_days=offset_days,
                enabled=True,
                minimum_interval_seconds=minimum_interval_seconds,
            )
        )

    return sorted(specs, key=lambda s: str(s.get("name", "")))


def build_auto_partition_change_propagation_specs() -> list[dict]:
    manifest = load_manifest()
    models = iter_models(manifest)

    specs_by_name: dict[str, dict] = {}
    duplicates: dict[str, list[str]] = defaultdict(list)

    for m in models:
        pc = get_luban_meta(m.meta).get("partition_change")
        if not isinstance(pc, dict):
            continue
        propagate = pc.get("propagate")
        if not isinstance(propagate, dict):
            continue

        enabled = bool(propagate.get("enabled", False))

        targets = propagate.get("targets")
        if not isinstance(targets, list) or not targets:
            raise ValueError(f"Partition-change propagate on model '{m.name}' requires non-empty targets")

        minimum_interval_seconds = int(propagate.get("minimum_interval_seconds", 30))
        name = propagate.get("name")

        for target in targets:
            if not isinstance(target, dict):
                raise ValueError(f"Partition-change propagate target must be dict (model '{m.name}')")
            job_name = target.get("job_name")
            if not job_name:
                raise ValueError(f"Partition-change propagate target missing job_name (model '{m.name}')")

            spec_name = name or f"{m.name}_partition_change_to_{job_name}"

            spec = partition_change_propagation(
                name=str(spec_name),
                upstream_dbt_model=m.name,
                job_name=str(job_name),
                enabled=enabled,
                minimum_interval_seconds=minimum_interval_seconds,
            )

            if spec["name"] in specs_by_name:
                duplicates[spec["name"]].append(m.name)
            specs_by_name[spec["name"]] = spec

    if duplicates:
        details = ", ".join([f"{name}: {sorted(models)}" for name, models in sorted(duplicates.items())])
        raise ValueError(f"Duplicate propagation spec names in dbt meta.luban.partition_change.propagate: {details}")

    return [specs_by_name[name] for name in sorted(specs_by_name.keys())]
