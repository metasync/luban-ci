from datetime import datetime

import importlib

partition_vars = importlib.import_module("{{cookiecutter.package_name}}.assets.lib.partition_vars")
_dbt_partition_vars_from_time_window = partition_vars._dbt_partition_vars_from_time_window
_get_dbt_vars_for_context = partition_vars._get_dbt_vars_for_context


class _FakeTimeWindow:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end


class _FakeContext:
    def __init__(self, start: datetime, end: datetime):
        # Dagster provides `context.partition_time_window` for time-window partitions.
        self.partition_time_window = _FakeTimeWindow(start, end)


def test_partition_vars_date_and_datetime_formats():
    start = datetime(2026, 1, 2, 0, 0, 0)
    end = datetime(2026, 1, 3, 0, 0, 0)
    vars_ = _dbt_partition_vars_from_time_window(start, end)
    assert vars_["min_date"] == "2026-01-02"
    assert vars_["max_date"] == "2026-01-03"
    assert vars_["min_datetime"] == "2026-01-02 00:00:00"
    assert vars_["max_datetime"] == "2026-01-03 00:00:00"


def test_get_dbt_vars_for_context_returns_vars_when_partitioned():
    ctx = _FakeContext(datetime(2026, 1, 2, 0, 0, 0), datetime(2026, 1, 3, 0, 0, 0))
    vars_ = _get_dbt_vars_for_context(ctx)
    assert vars_ is not None
    assert vars_["min_date"] == "2026-01-02"
