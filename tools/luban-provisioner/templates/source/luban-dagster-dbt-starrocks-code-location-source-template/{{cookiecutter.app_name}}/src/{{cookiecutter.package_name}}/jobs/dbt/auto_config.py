from __future__ import annotations

from collections import defaultdict

from ...dbt.manifest import first_tag_value, get_luban_meta, iter_models, load_manifest
from .presets import models_job


def build_auto_dbt_job_specs() -> list[dict]:
    manifest = load_manifest()
    models = iter_models(manifest)

    grouped_models: dict[str, list[str]] = defaultdict(list)
    grouped_include_upstream: dict[str, bool] = {}
    grouped_partitions: dict[str, str | None] = {}

    for m in models:
        job_name, include_upstream, partitions = extract_job_config(m)
        if not job_name:
            continue

        grouped_models[job_name].append(m.name)

        if job_name in grouped_include_upstream and grouped_include_upstream[job_name] != include_upstream:
            raise ValueError(f"Conflicting include_upstream for job '{job_name}'")
        grouped_include_upstream[job_name] = include_upstream

        if job_name in grouped_partitions and grouped_partitions[job_name] != partitions:
            raise ValueError(f"Conflicting partitions for job '{job_name}'")
        grouped_partitions[job_name] = partitions

    specs: list[dict] = []
    for job_name in sorted(grouped_models.keys()):
        models_list = sorted(set(grouped_models[job_name]))
        specs.append(
            models_job(
                name=job_name,
                models=models_list,
                include_upstream=grouped_include_upstream.get(job_name, False),
                partitions=grouped_partitions.get(job_name),
            )
        )

    return specs


def extract_job_config(model) -> tuple[str | None, bool, str | None]:
    meta = model.meta
    tags = model.tags

    job_meta = get_luban_meta(meta).get("job")
    if isinstance(job_meta, dict):
        job_name = job_meta.get("name")
        if job_name:
            include_upstream = bool(job_meta.get("include_upstream", False))
            partitions = job_meta.get("partitions")
            if partitions is None:
                partitions = "daily" if "daily" in tags else None
            return str(job_name), include_upstream, partitions

    job_name_from_tag = first_tag_value(tags, prefix="job:")
    if job_name_from_tag:
        return str(job_name_from_tag), False, ("daily" if "daily" in tags else None)

    if "asset_job" in tags:
        return f"dbt_{model.name}_asset_job", False, ("daily" if "daily" in tags else None)

    return None, False, None
