from datetime import timedelta

import dagster as dg


def _with_optional_tick_suffix(*, run_key: str, scheduled_time, dedupe_across_ticks: bool) -> str:
    if dedupe_across_ticks:
        return run_key
    return f"{run_key}:{scheduled_time.strftime('%Y%m%dT%H%M%S')}"


def _build_daily_partitioned_schedule(
    *,
    name: str,
    cron_schedule: str,
    job,
    partition_offset_days: int,
    partition_lookback_days: int,
    dedupe_across_ticks: bool,
    default_status: dg.DefaultScheduleStatus,
):
    @dg.schedule(
        name=name,
        cron_schedule=cron_schedule,
        job=job,
        default_status=default_status,
    )
    def _schedule(context):
        scheduled_time = context.scheduled_execution_time or dg.get_current_datetime()

        anchor_day = (scheduled_time - timedelta(days=partition_offset_days)).date()
        run_requests = []
        for i in range(partition_lookback_days + 1):
            partition_day = (anchor_day - timedelta(days=i)).isoformat()
            run_key = _with_optional_tick_suffix(
                run_key=f"{name}:{partition_day}",
                scheduled_time=scheduled_time,
                dedupe_across_ticks=dedupe_across_ticks,
            )
            run_requests.append(
                dg.RunRequest(
                    partition_key=partition_day,
                    run_key=run_key,
                )
            )
        return run_requests

    return _schedule


def _build_hourly_partitioned_schedule(
    *,
    name: str,
    cron_schedule: str,
    job,
    partition_offset_hours: int,
    partition_lookback_hours: int,
    dedupe_across_ticks: bool,
    default_status: dg.DefaultScheduleStatus,
):
    @dg.schedule(
        name=name,
        cron_schedule=cron_schedule,
        job=job,
        default_status=default_status,
    )
    def _schedule(context):
        scheduled_time = context.scheduled_execution_time or dg.get_current_datetime()

        anchor_hour = (scheduled_time - timedelta(hours=partition_offset_hours)).replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        run_requests = []
        for i in range(partition_lookback_hours + 1):
            partition_hour = anchor_hour - timedelta(hours=i)
            partition_key = partition_hour.strftime("%Y-%m-%d-%H:%M")
            run_key = _with_optional_tick_suffix(
                run_key=f"{name}:{partition_key}",
                scheduled_time=scheduled_time,
                dedupe_across_ticks=dedupe_across_ticks,
            )
            run_requests.append(
                dg.RunRequest(
                    partition_key=partition_key,
                    run_key=run_key,
                )
            )
        return run_requests

    return _schedule


def build_dbt_schedules(schedule_specs, jobs_by_name):
    duplicated = set()
    seen = set()
    for spec in schedule_specs:
        name = spec.get("name")
        if not name:
            continue
        if name in seen:
            duplicated.add(name)
        else:
            seen.add(name)
    if duplicated:
        raise ValueError(f"Duplicate dbt schedule names: {sorted(duplicated)}")

    schedules_by_name = {}
    for spec in schedule_specs:
        enabled = bool(spec.get("enabled", True))
        default_status = (
            dg.DefaultScheduleStatus.RUNNING if enabled else dg.DefaultScheduleStatus.STOPPED
        )

        job = jobs_by_name[spec["job_name"]]
        partition_type = spec.get("partition_type", "daily")
        dedupe_across_ticks = bool(spec.get("dedupe_across_ticks", True))

        if partition_type == "daily":
            partition_offset_hours = int(spec.get("partition_offset_hours", 0))
            partition_lookback_hours = int(spec.get("partition_lookback_hours", 0))
            if partition_offset_hours != 0 or partition_lookback_hours != 0:
                raise ValueError(
                    f"Daily schedule '{spec['name']}' cannot set hourly offset/lookback fields"
                )

            partition_offset_days = int(spec.get("partition_offset_days", 0))
            partition_lookback_days = int(spec.get("partition_lookback_days", 0))
            schedules_by_name[spec["name"]] = _build_daily_partitioned_schedule(
                name=spec["name"],
                cron_schedule=spec["cron_schedule"],
                job=job,
                partition_offset_days=partition_offset_days,
                partition_lookback_days=partition_lookback_days,
                dedupe_across_ticks=dedupe_across_ticks,
                default_status=default_status,
            )
            continue

        if partition_type == "hourly":
            partition_offset_days = int(spec.get("partition_offset_days", 0))
            partition_lookback_days = int(spec.get("partition_lookback_days", 0))
            if partition_offset_days != 0 or partition_lookback_days != 0:
                raise ValueError(
                    f"Hourly schedule '{spec['name']}' cannot set daily offset/lookback fields"
                )

            partition_offset_hours = int(spec.get("partition_offset_hours", 0))
            partition_lookback_hours = int(spec.get("partition_lookback_hours", 0))
            schedules_by_name[spec["name"]] = _build_hourly_partitioned_schedule(
                name=spec["name"],
                cron_schedule=spec["cron_schedule"],
                job=job,
                partition_offset_hours=partition_offset_hours,
                partition_lookback_hours=partition_lookback_hours,
                dedupe_across_ticks=dedupe_across_ticks,
                default_status=default_status,
            )
            continue

        raise ValueError(f"Unsupported partition_type: {partition_type}")

    return list(schedules_by_name.values())
