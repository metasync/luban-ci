import os
import time
from typing import Iterable, Optional

from dagster import DagsterInstance, DagsterRunStatus, RunsFilter
from opentelemetry import metrics
from opentelemetry.metrics import Observation

from luban_dagster_platform.otel import configure_otel

from dagster._core.definitions.run_request import InstigatorType
from dagster._core.scheduler.instigation import InstigatorStatus


def _enabled(value: Optional[str]) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized not in {"", "none", "false", "0"}


def _run_count(instance: DagsterInstance, statuses: Iterable[DagsterRunStatus]) -> int:
    return instance.get_runs_count(RunsFilter(statuses=list(statuses)))


def _oldest_run_age_seconds(instance: DagsterInstance, statuses: Iterable[DagsterRunStatus]) -> float:
    records = instance.get_run_records(
        RunsFilter(statuses=list(statuses)),
        limit=1,
        order_by="create_timestamp",
        ascending=True,
    )
    if not records:
        return 0.0

    now = time.time()
    return max(0.0, now - (records[0].create_timestamp or now))


def _daemon_heartbeat_ages_seconds(instance: DagsterInstance) -> dict[str, float]:
    now = time.time()
    ages_by_type: dict[str, float] = {}

    for heartbeat in instance.get_daemon_heartbeats().values():
        daemon_type = heartbeat.daemon_type
        age = max(0.0, now - heartbeat.timestamp)
        if daemon_type not in ages_by_type or age < ages_by_type[daemon_type]:
            ages_by_type[daemon_type] = age

    return ages_by_type


def _daemon_heartbeat_error_counts(instance: DagsterInstance) -> dict[str, int]:
    counts_by_type: dict[str, int] = {}
    for heartbeat in instance.get_daemon_heartbeats().values():
        daemon_type = heartbeat.daemon_type
        counts_by_type[daemon_type] = counts_by_type.get(daemon_type, 0) + len(heartbeat.errors or [])
    return counts_by_type


def _instigator_selector_id(state) -> str:
    repo_origin = getattr(state.origin, "repository_origin", None)
    if repo_origin is not None and hasattr(repo_origin, "get_selector_id"):
        return repo_origin.get_selector_id()
    return state.origin.get_id()


def _instigator_last_tick_age_seconds(instance: DagsterInstance, state) -> Optional[float]:
    origin_id = state.origin.get_id()
    selector_id = _instigator_selector_id(state)

    try:
        ticks = instance.get_ticks(origin_id=origin_id, selector_id=selector_id, limit=1)
    except Exception:
        ticks = instance.get_ticks(origin_id=origin_id, selector_id=origin_id, limit=1)

    if not ticks:
        return None

    now = time.time()
    return max(0.0, now - ticks[0].timestamp)


def main() -> None:
    export_interval_millis = int(os.getenv("LUBAN_OTEL_METRICS_EXPORT_INTERVAL_MILLIS") or "60000")
    if not _enabled(os.getenv("OTEL_METRICS_EXPORTER")):
        while True:
            time.sleep(3600)

    configure_otel(export_interval_millis=export_interval_millis)

    instance = DagsterInstance.get()
    meter = metrics.get_meter("luban.dagster.platform")

    def queued_cb(_options):
        yield Observation(_run_count(instance, [DagsterRunStatus.QUEUED]))

    def queued_oldest_age_cb(_options):
        yield Observation(_oldest_run_age_seconds(instance, [DagsterRunStatus.QUEUED]))

    def in_progress_cb(_options):
        yield Observation(
            _run_count(
                instance,
                [
                    DagsterRunStatus.NOT_STARTED,
                    DagsterRunStatus.STARTING,
                    DagsterRunStatus.STARTED,
                ],
            )
        )

    def sensors_enabled_cb(_options):
        states = instance.all_instigator_state(instigator_type=InstigatorType.SENSOR)
        yield Observation(sum(1 for s in states if s.status == InstigatorStatus.RUNNING))

    def schedules_enabled_cb(_options):
        states = instance.all_instigator_state(instigator_type=InstigatorType.SCHEDULE)
        yield Observation(sum(1 for s in states if s.status == InstigatorStatus.RUNNING))

    def sensor_last_tick_age_cb(_options):
        states = instance.all_instigator_state(instigator_type=InstigatorType.SENSOR)
        for s in states:
            age = _instigator_last_tick_age_seconds(instance, s)
            if age is None:
                continue
            yield Observation(
                age,
                attributes={
                    "dagster.instigator_name": s.origin.instigator_name,
                    "dagster.instigator_status": s.status.value,
                },
            )

    def schedule_last_tick_age_cb(_options):
        states = instance.all_instigator_state(instigator_type=InstigatorType.SCHEDULE)
        for s in states:
            age = _instigator_last_tick_age_seconds(instance, s)
            if age is None:
                continue
            yield Observation(
                age,
                attributes={
                    "dagster.instigator_name": s.origin.instigator_name,
                    "dagster.instigator_status": s.status.value,
                },
            )

    meter.create_observable_gauge(
        "dagster.run.queue.depth",
        callbacks=[queued_cb],
        unit="1",
    )
    meter.create_observable_gauge(
        "dagster.run.queue.oldest_age_seconds",
        callbacks=[queued_oldest_age_cb],
        unit="s",
    )
    meter.create_observable_gauge(
        "dagster.run.in_progress.count",
        callbacks=[in_progress_cb],
        unit="1",
    )
    meter.create_observable_gauge(
        "dagster.sensor.enabled.count",
        callbacks=[sensors_enabled_cb],
        unit="1",
    )
    meter.create_observable_gauge(
        "dagster.schedule.enabled.count",
        callbacks=[schedules_enabled_cb],
        unit="1",
    )
    meter.create_observable_gauge(
        "dagster.sensor.last_tick_age_seconds",
        callbacks=[sensor_last_tick_age_cb],
        unit="s",
    )
    meter.create_observable_gauge(
        "dagster.schedule.last_tick_age_seconds",
        callbacks=[schedule_last_tick_age_cb],
        unit="s",
    )

    def daemon_heartbeats_count_cb(_options):
        yield Observation(len(instance.get_daemon_heartbeats()))

    def daemon_heartbeat_age_cb(_options):
        for daemon_type, age in _daemon_heartbeat_ages_seconds(instance).items():
            yield Observation(age, attributes={"dagster.daemon_type": daemon_type})

    def daemon_heartbeat_errors_cb(_options):
        for daemon_type, count in _daemon_heartbeat_error_counts(instance).items():
            yield Observation(count, attributes={"dagster.daemon_type": daemon_type})

    meter.create_observable_gauge(
        "dagster.daemon.heartbeat.count",
        callbacks=[daemon_heartbeats_count_cb],
        unit="1",
    )
    meter.create_observable_gauge(
        "dagster.daemon.heartbeat_age_seconds",
        callbacks=[daemon_heartbeat_age_cb],
        unit="s",
    )
    meter.create_observable_gauge(
        "dagster.daemon.heartbeat_errors.count",
        callbacks=[daemon_heartbeat_errors_cb],
        unit="1",
    )

    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
