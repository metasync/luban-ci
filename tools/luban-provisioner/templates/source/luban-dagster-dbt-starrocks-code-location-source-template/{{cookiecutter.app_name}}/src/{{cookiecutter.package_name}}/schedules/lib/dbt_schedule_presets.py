def cron_schedule(*, name: str, cron: str, job_name: str, enabled: bool = True):
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
    }


def daily_at(*, name: str, job_name: str, hour: int = 1, minute: int = 0, enabled: bool = True):
    if not (0 <= hour <= 23):
        raise ValueError("hour must be between 0 and 23")
    if not (0 <= minute <= 59):
        raise ValueError("minute must be between 0 and 59")

    return cron_schedule(
        name=name,
        cron=f"{minute} {hour} * * *",
        job_name=job_name,
        enabled=enabled,
    )


def hourly_at(*, name: str, job_name: str, minute: int = 0, enabled: bool = False):
    if not (0 <= minute <= 59):
        raise ValueError("minute must be between 0 and 59")

    return cron_schedule(
        name=name,
        cron=f"{minute} * * * *",
        job_name=job_name,
        enabled=enabled,
    )

