def daily_partition_change(
    *,
    name: str,
    job_name: str,
    detector_model: str,
    lookback_days: int,
    offset_days: int = 0,
    enabled: bool = True,
    minimum_interval_seconds: int = 60,
):
    if not name:
        raise ValueError("Sensor name must be non-empty")
    if not job_name:
        raise ValueError("job_name must be non-empty")
    if not detector_model:
        raise ValueError("detector_model must be non-empty")
    if lookback_days < 0:
        raise ValueError("lookback_days must be >= 0")
    if offset_days < 0:
        raise ValueError("offset_days must be >= 0")
    if minimum_interval_seconds <= 0:
        raise ValueError("minimum_interval_seconds must be > 0")

    return {
        "partition_type": "daily",
        "name": name,
        "job_name": job_name,
        "detector_model": detector_model,
        "lookback_days": lookback_days,
        "offset_days": offset_days,
        "enabled": enabled,
        "minimum_interval_seconds": minimum_interval_seconds,
    }

