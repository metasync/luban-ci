"""Dynamic partition dispatcher (reusable builder).

Goal: one sensor + job + partitions definition per dynamic-partition pipeline.

Semantics:
- Tick: evaluate once per minute
- Collect: for each source, query incrementally using a watermark, extract partition keys, then union + dedupe
- Dispatch: dispatch runs only at slot boundaries (one run per key; include pipeline info in run_key for idempotency across pipelines)
- Reconcile: reconcile per-key run success/failure; failed/missing runs go back to pending

Cursor (UTC) key state:
- last_collect_ts_by_source: per-source watermark (avoid sources interfering with each other)
- pending: keys waiting to be dispatched (set semantics)
- inflight: dispatched but not yet finalized keys (with run_key/slot)
- attempts: retry counts
- last_dispatch_slot: prevent double-dispatch within the same slot

Source modes:
- table_keys: extract keys from a table (key_column or key_expression)
- lookback: if the source table changed within the window, backfill keys for the last N days (useful for dimension tables)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import dagster as dg

try:
    from dagster import DagsterRunStatus, RunsFilter
except Exception:
    from dagster._core.storage.dagster_run import DagsterRunStatus
    from dagster._core.storage.pipeline_run import RunsFilter

SENSOR_CURSOR_VERSION = 3

DEFAULT_TS = "1970-01-01 00:00:00"
TS_FMT = "%Y-%m-%d %H:%M:%S"

TAG_SLOT = "luban/slot"
TAG_PARTITION_KEY = "luban/partition_key"
TAG_MODE = "luban/mode"
TAG_PIPELINE = "luban/pipeline"

ENV_SLOT_SECONDS = "LUBAN_DYNAMIC_DISPATCH_SLOT_SECONDS"
ENV_MAX_KEYS_PER_TICK = "LUBAN_DYNAMIC_MAX_KEYS_PER_TICK"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _format_ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime(TS_FMT)


def _quoted(identifier: str) -> str:
    return "`" + identifier.replace("`", "``") + "`"


def _slot_floor(dt: datetime, slot_seconds: int) -> datetime:
    epoch = int(dt.timestamp())
    floored = (epoch // slot_seconds) * slot_seconds
    return datetime.fromtimestamp(floored, tz=timezone.utc).replace(microsecond=0)


def _slot_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
# v: cursor schema version
# last_collect_ts_default: fallback timestamp (e.g. first run or missing per-source watermark)
# last_collect_ts_by_source: per-source watermark (source_id -> ts)
class _CursorState:
    v: int
    last_collect_ts_default: str
    last_collect_ts_by_source: dict[str, str]
    pending: set[str]
    inflight: dict[str, dict]
    attempts: dict[str, int]
    last_dispatch_slot: str | None
    last_dispatch_day: str | None


def _load_cursor(cursor: str | None) -> _CursorState:
    if not cursor:
        return _CursorState(
            v=SENSOR_CURSOR_VERSION,
            last_collect_ts_default=DEFAULT_TS,
            last_collect_ts_by_source={},
            pending=set(),
            inflight={},
            attempts={},
            last_dispatch_slot=None,
            last_dispatch_day=None,
        )
    try:
        raw = json.loads(cursor)
        pending = set(raw.get("pending") or [])
        inflight = raw.get("inflight") or {}
        attempts = raw.get("attempts") or {}
        attempts = {str(k): int(v) for k, v in attempts.items()}
        last_dispatch_slot = raw.get("last_dispatch_slot")
        last_dispatch_day = raw.get("last_dispatch_day")

        last_collect_ts_default = raw.get("last_collect_ts_default") or raw.get("last_collect_ts") or DEFAULT_TS
        last_collect_ts_by_source = raw.get("last_collect_ts_by_source") or {}
        last_collect_ts_by_source = {str(k): str(v) for k, v in last_collect_ts_by_source.items() if v is not None}

        return _CursorState(
            v=int(raw.get("v") or SENSOR_CURSOR_VERSION),
            last_collect_ts_default=str(last_collect_ts_default),
            last_collect_ts_by_source=last_collect_ts_by_source,
            pending={str(x) for x in pending},
            inflight={str(k): v for k, v in inflight.items()},
            attempts=attempts,
            last_dispatch_slot=str(last_dispatch_slot) if last_dispatch_slot else None,
            last_dispatch_day=str(last_dispatch_day) if last_dispatch_day else None,
        )
    except Exception:
        return _CursorState(
            v=SENSOR_CURSOR_VERSION,
            last_collect_ts_default=DEFAULT_TS,
            last_collect_ts_by_source={},
            pending=set(),
            inflight={},
            attempts={},
            last_dispatch_slot=None,
            last_dispatch_day=None,
        )


def _dump_cursor(state: _CursorState) -> str:
    payload = {
        "v": SENSOR_CURSOR_VERSION,
        "last_collect_ts_default": state.last_collect_ts_default,
        "last_collect_ts_by_source": state.last_collect_ts_by_source,
        "pending": sorted(state.pending),
        "inflight": state.inflight,
        "attempts": state.attempts,
        "last_dispatch_slot": state.last_dispatch_slot,
        "last_dispatch_day": state.last_dispatch_day,
    }
    return json.dumps(payload, sort_keys=True)


def _resolve_db_name_from_source(source: dict) -> str:
    db_env_var = source.get("db_env_var")
    db_default = source.get("db_default")

    if db_env_var:
        value = os.getenv(str(db_env_var))
        if value:
            return str(value)

    if db_default is not None and str(db_default):
        return str(db_default)

    return ""



def _resolve_catalog_name_from_source(source: dict) -> str:
    catalog_env_var = source.get("catalog_env_var")
    catalog_default = source.get("catalog")

    if catalog_env_var:
        value = os.getenv(str(catalog_env_var))
        if value:
            return str(value)

    if catalog_default is not None and str(catalog_default):
        return str(catalog_default)

    return ""


def _qualified_table_ref(*, catalog: str, db: str, table: str) -> str:
    if catalog:
        return f"{_quoted(catalog)}.{_quoted(db)}.{_quoted(table)}"
    return f"{_quoted(db)}.{_quoted(table)}"


def _collect_keys_for_source(
    context: dg.SensorEvaluationContext,
    *,
    source: dict,
    from_ts: str,
    now_ts: str,
    max_keys_per_tick: int,
) -> list[str]:
    # source spec：
    # - mode=table_keys：需要 table + updated_at_column + (key_column|key_expression)
    # - mode=lookback：需要 table + updated_at_column + lookback_days

    mode = str(source.get("mode") or "table_keys")
    if mode not in {"table_keys", "lookback"}:
        raise ValueError(f"unsupported source mode: {mode}")

    catalog = _resolve_catalog_name_from_source(source)
    db = _resolve_db_name_from_source(source)
    table = str(source.get("table") or "")
    updated_at_col = str(source.get("updated_at_column") or "updated_at")
    where_extra = source.get("where")

    if not db or not table:
        raise ValueError(
            f"invalid source db/table (catalog/catalog_env_var/db_env_var/db_default/table): {source}"
        )

    from_ref = _qualified_table_ref(catalog=catalog, db=db, table=table)

    if mode != "lookback":
        key_column = source.get("key_column")
        key_expression = source.get("key_expression")
        if key_column:
            key_expr = _quoted(str(key_column))
        elif key_expression:
            key_expr = str(key_expression)
        else:
            raise ValueError(f"source must set key_column or key_expression: {source}")

    if mode == "lookback":
        lookback_days = int(source.get("lookback_days") or 0)
        if lookback_days <= 0:
            return []

        sql = (
            f"select count(*) "
            f"from {from_ref} "
            f"where {_quoted(updated_at_col)} >= '{from_ts}' "
            f"and {_quoted(updated_at_col)} < '{now_ts}'"
        )
        if where_extra:
            sql += f" and ({where_extra})"

        try:
            changed = context.resources.starrocks.query_scalar(sql)
        except Exception as e:
            raise ValueError(f"failed to query lookback change check. sql={sql}") from e
        if not changed or int(changed) <= 0:
            return []

        anchor = _utcnow().date()
        return [(anchor - timedelta(days=i)).isoformat() for i in range(lookback_days + 1)]

    sql = (
        f"select distinct {key_expr} "
        f"from {from_ref} "
        f"where {_quoted(updated_at_col)} >= '{from_ts}' "
        f"and {_quoted(updated_at_col)} < '{now_ts}'"
    )
    if where_extra:
        sql += f" and ({where_extra})"

    try:
        keys = context.resources.starrocks.query_column(sql)
    except Exception as e:
        raise ValueError(f"failed to query partition keys. sql={sql}") from e
    keys = [str(k) for k in keys if k is not None and str(k) != ""]
    if max_keys_per_tick > 0:
        keys = keys[:max_keys_per_tick]
    return keys


def _collect_keys_multi(
    context: dg.SensorEvaluationContext,
    *,
    state: _CursorState,
    sources: list[dict],
    max_keys_per_tick: int,
) -> tuple[list[str], str]:
    now_ts = _format_ts(_utcnow())

    collected: list[str] = []
    for source in sources:
        source_id = str(source.get("source_id") or "")
        if not source_id:
            continue

        from_ts = state.last_collect_ts_by_source.get(source_id) or state.last_collect_ts_default or DEFAULT_TS
        keys = _collect_keys_for_source(
            context,
            source=source,
            from_ts=str(from_ts),
            now_ts=now_ts,
            max_keys_per_tick=max_keys_per_tick,
        )
        collected.extend(keys)
        state.last_collect_ts_by_source[source_id] = now_ts

    state.last_collect_ts_default = now_ts

    seen = set()
    deduped = []
    for k in collected:
        if k in seen:
            continue
        seen.add(k)
        deduped.append(k)

    if max_keys_per_tick > 0:
        deduped = deduped[:max_keys_per_tick]

    return deduped, now_ts


def _get_run_status_by_run_key(context: dg.SensorEvaluationContext, run_key: str) -> DagsterRunStatus | None:
    runs = context.instance.get_runs(filters=RunsFilter(tags={"dagster/run_key": run_key}))
    if not runs:
        return None

    statuses = [r.status for r in runs]
    if DagsterRunStatus.SUCCESS in statuses:
        return DagsterRunStatus.SUCCESS
    if DagsterRunStatus.FAILURE in statuses:
        return DagsterRunStatus.FAILURE
    if DagsterRunStatus.CANCELED in statuses:
        return DagsterRunStatus.CANCELED
    return statuses[0]


def _reconcile(context: dg.SensorEvaluationContext, state: _CursorState) -> None:
    inflight_items = list(state.inflight.items())
    for key, info in inflight_items:
        run_key = info.get("run_key")
        if not run_key:
            state.inflight.pop(key, None)
            state.attempts[key] = int(state.attempts.get(key, 0)) + 1
            state.pending.add(key)
            continue

        status = _get_run_status_by_run_key(context, run_key)

        if status == DagsterRunStatus.SUCCESS:
            state.inflight.pop(key, None)
            state.pending.discard(key)
            state.attempts.pop(key, None)
            continue

        if status in {DagsterRunStatus.FAILURE, DagsterRunStatus.CANCELED} or status is None:
            state.inflight.pop(key, None)
            state.attempts[key] = int(state.attempts.get(key, 0)) + 1
            state.pending.add(key)
            continue


def _next_dispatch_slot(now: datetime, state: _CursorState, slot_seconds: int) -> datetime | None:
    current_slot = _slot_floor(now, slot_seconds)

    if state.last_dispatch_slot is None:
        return None

    last = datetime.fromisoformat(state.last_dispatch_slot.replace("Z", "+00:00")).astimezone(timezone.utc)
    last_slot = _slot_floor(last, slot_seconds)

    if current_slot > last_slot:
        return current_slot

    return None


def build_dynamic_partition_dispatcher_sensor(
    *,
    sensor_name: str,
    job,
    partitions_def_name: str,
    sources: list[dict],
    dispatch_daily_utc_hour: int | None,
    dispatch_slot_seconds: int | None,
    max_keys_per_tick: int | None,
    default_status: str,
):
    # 每條動態管線用這個 builder 建一個 sensor：
    # - partitions_def_name：該管線獨立的 DynamicPartitionsDefinition 名稱
    # - sources：多來源收 key（union），watermark 存在 cursor
    # - dispatch_slot_seconds：控制派發頻率（collect 仍是每分鐘）

    status = str(default_status or "RUNNING").upper()
    sensor_default_status = (
        dg.DefaultSensorStatus.RUNNING if status == "RUNNING" else dg.DefaultSensorStatus.STOPPED
    )

    partitions_def = dg.DynamicPartitionsDefinition(name=partitions_def_name)

    @dg.sensor(
        name=sensor_name,
        job=job,
        minimum_interval_seconds=60,
        required_resource_keys={"starrocks"},
        default_status=sensor_default_status,
    )
    def _sensor(context: dg.SensorEvaluationContext):
        state = _load_cursor(context.cursor)

        _reconcile(context, state)

        collected_keys, _ = _collect_keys_multi(
            context,
            state=state,
            sources=sources,
            max_keys_per_tick=int(max_keys_per_tick or 5000),
        )
        for k in collected_keys:
            state.pending.add(k)

        dynamic_requests: list[dg.AddDynamicPartitionsRequest] = []
        if collected_keys:
            try:
                existing = set(context.instance.get_dynamic_partitions(partitions_def_name))
            except Exception:
                existing = set()

            to_add = [k for k in collected_keys if k not in existing]
            if to_add:
                dynamic_requests.append(partitions_def.build_add_request(to_add))

        run_requests: list[dg.RunRequest] = []
        now = _utcnow()

        if dispatch_daily_utc_hour is not None:
            hour = int(dispatch_daily_utc_hour)
            today = now.date().isoformat()
            slot_dt = now.replace(hour=hour, minute=0, second=0, microsecond=0)

            if now.hour >= hour and state.last_dispatch_day != today and state.pending:
                slot = _slot_str(slot_dt)

                dispatchable = sorted(state.pending - set(state.inflight.keys()))
                for key in dispatchable:
                    run_key = f"{slot}:{sensor_name}:{key}"
                    run_requests.append(
                        dg.RunRequest(
                            run_key=run_key,
                            partition_key=key,
                            tags={
                                TAG_SLOT: slot,
                                TAG_PARTITION_KEY: key,
                                TAG_MODE: "dispatch",
                                TAG_PIPELINE: sensor_name,
                            },
                        )
                    )
                    state.inflight[key] = {"slot": slot, "run_key": run_key}

                state.last_dispatch_slot = slot
                state.last_dispatch_day = today

        else:
            slot_seconds = (
                int(dispatch_slot_seconds)
                if dispatch_slot_seconds is not None
                else int(os.getenv(ENV_SLOT_SECONDS, "3600"))
            )

            if state.last_dispatch_slot is None:
                state.last_dispatch_slot = _slot_str(_slot_floor(now, slot_seconds))
                slot_dt = None
            else:
                slot_dt = _next_dispatch_slot(now, state, slot_seconds)

            if slot_dt is not None and state.pending:
                slot = _slot_str(slot_dt)

                dispatchable = sorted(state.pending - set(state.inflight.keys()))
                for key in dispatchable:
                    run_key = f"{slot}:{sensor_name}:{key}"
                    run_requests.append(
                        dg.RunRequest(
                            run_key=run_key,
                            partition_key=key,
                            tags={
                                TAG_SLOT: slot,
                                TAG_PARTITION_KEY: key,
                                TAG_MODE: "dispatch",
                                TAG_PIPELINE: sensor_name,
                            },
                        )
                    )
                    state.inflight[key] = {"slot": slot, "run_key": run_key}

                state.last_dispatch_slot = slot

        next_cursor = _dump_cursor(state)

        if not run_requests and not dynamic_requests and not collected_keys:
            return dg.SensorResult(skip_reason="no_changes", cursor=next_cursor)

        return dg.SensorResult(
            run_requests=run_requests,
            dynamic_partitions_requests=dynamic_requests,
            cursor=next_cursor,
        )

    return _sensor
