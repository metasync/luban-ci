def partition_change_propagation(
    *,
    name: str,
    upstream_dbt_model: str,
    job_name: str,
    enabled: bool = False,
    minimum_interval_seconds: int = 30,
):
    if not name:
        raise ValueError("Sensor name must be non-empty")
    if not upstream_dbt_model:
        raise ValueError("upstream_dbt_model must be non-empty")
    if not job_name:
        raise ValueError("job_name must be non-empty")
    if minimum_interval_seconds <= 0:
        raise ValueError("minimum_interval_seconds must be > 0")

    return {
        "name": name,
        "upstream_dbt_model": upstream_dbt_model,
        "job_name": job_name,
        "enabled": enabled,
        "minimum_interval_seconds": minimum_interval_seconds,
    }

