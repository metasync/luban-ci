from datetime import datetime


def _dbt_partition_vars_from_time_window(start: datetime, end: datetime) -> dict[str, str]:
    min_date = start.date().strftime("%Y-%m-%d")
    max_date = end.date().strftime("%Y-%m-%d")
    min_datetime = start.strftime("%Y-%m-%d %H:%M:%S")
    max_datetime = end.strftime("%Y-%m-%d %H:%M:%S")

    return {
        "min_date": min_date,
        "max_date": max_date,
        "min_datetime": min_datetime,
        "max_datetime": max_datetime,
    }


def _get_dbt_vars_for_context(context) -> dict[str, str] | None:
    try:
        time_window = context.partition_time_window
        if time_window is not None:
            return _dbt_partition_vars_from_time_window(time_window.start, time_window.end)
    except Exception:
        pass

    try:
        partition_key = context.partition_key
    except Exception:
        return None

    if not partition_key:
        return None

    return {"partition_key": str(partition_key)}

