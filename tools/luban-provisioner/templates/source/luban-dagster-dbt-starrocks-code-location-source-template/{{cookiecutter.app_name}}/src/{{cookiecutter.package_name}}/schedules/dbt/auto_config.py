from __future__ import annotations

from collections import defaultdict

from ...dbt.manifest import get_luban_meta, iter_models, load_manifest
from ...jobs.dbt.auto_config import extract_job_config
from .presets import daily_at


def build_auto_dbt_schedule_specs() -> list[dict]:
    manifest = load_manifest()
    models = iter_models(manifest)

    specs_by_name: dict[str, dict] = {}
    duplicates: dict[str, list[str]] = defaultdict(list)

    for m in models:
        schedule_meta = get_luban_meta(m.meta).get("asset_schedule")
        if not isinstance(schedule_meta, dict):
            continue

        schedule_name = schedule_meta.get("name")
        if not schedule_name:
            raise ValueError(f"Model '{m.name}' has meta.luban.asset_schedule but missing name")

        derived_job_name, _, _ = extract_job_config(m)
        if not derived_job_name:
            raise ValueError(
                f"Asset schedule '{schedule_name}' on model '{m.name}' could not derive job_name; add tag 'asset_job', tag 'job:<name>', or meta.luban.job"
            )
        job_name = derived_job_name

        schedule_type = schedule_meta.get("type", "daily_at")
        if schedule_type != "daily_at":
            raise ValueError(f"Unsupported schedule type: {schedule_type} (schedule '{schedule_name}')")

        lookback_days = int(schedule_meta.get("lookback_days", 0))
        hour = int(schedule_meta.get("hour", 1))
        minute = int(schedule_meta.get("minute", 0))
        enabled = bool(schedule_meta.get("enabled", True))

        spec = daily_at(
            name=str(schedule_name),
            job_name=str(job_name),
            lookback_days=lookback_days,
            hour=hour,
            minute=minute,
            enabled=enabled,
        )

        if spec["name"] in specs_by_name:
            duplicates[spec["name"]].append(m.name)
        specs_by_name[spec["name"]] = spec

    if duplicates:
        details = ", ".join([f"{name}: {sorted(models)}" for name, models in sorted(duplicates.items())])
        raise ValueError(f"Duplicate schedule names in dbt meta.luban.asset_schedule: {details}")

    return [specs_by_name[name] for name in sorted(specs_by_name.keys())]
