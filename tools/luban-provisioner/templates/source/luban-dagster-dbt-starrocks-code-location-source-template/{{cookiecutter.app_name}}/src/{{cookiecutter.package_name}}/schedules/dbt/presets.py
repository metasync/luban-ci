def _schedule_base(*, name: str, cron: str, job_name: str, enabled: bool, dedupe_across_ticks: bool):
    if not name:
        raise ValueError("Schedule name must be non-empty")
    if not cron:
        raise ValueError("Cron must be non-empty")
    if not job_name:
        raise ValueError("Job name must be non-empty")

    return {
        "name": name,
        "cron_schedule": cron,
        "job_name": job_name,
        "enabled": enabled,
        "dedupe_across_ticks": dedupe_across_ticks,
    }


def daily_cron_schedule(
    *,
    name: str,
    cron: str,
    job_name: str,
    enabled: bool = True,
    partition_offset_days: int = 0,
    partition_lookback_days: int = 0,
    dedupe_across_ticks: bool = True,
):
    if partition_offset_days < 0:
        raise ValueError("partition_offset_days must be >= 0")
    if partition_lookback_days < 0:
        raise ValueError("partition_lookback_days must be >= 0")

    return {
        **_schedule_base(
            name=name,
            cron=cron,
            job_name=job_name,
            enabled=enabled,
            dedupe_across_ticks=dedupe_across_ticks,
        ),
        "partition_type": "daily",
        "partition_offset_days": partition_offset_days,
        "partition_lookback_days": partition_lookback_days,
    }


def daily_at(
    *,
    name: str,
    job_name: str,
    lookback_days: int = 0,
    hour: int = 1,
    minute: int = 0,
    enabled: bool = True,
):
    if lookback_days < 0:
        raise ValueError("lookback_days must be >= 0")

    if not (0 <= hour <= 23):
        raise ValueError("hour must be between 0 and 23")
    if not (0 <= minute <= 59):
        raise ValueError("minute must be between 0 and 59")

    return daily_cron_schedule(
        name=name,
        cron=f"{minute} {hour} * * *",
        job_name=job_name,
        enabled=enabled,
        partition_offset_days=1,
        partition_lookback_days=lookback_days,
        dedupe_across_ticks=True,
    )

