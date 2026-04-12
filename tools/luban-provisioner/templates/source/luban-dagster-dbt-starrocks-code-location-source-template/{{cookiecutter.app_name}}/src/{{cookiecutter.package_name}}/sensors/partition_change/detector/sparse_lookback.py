from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any


@dataclass(frozen=True)
class SparseLookbackImpactRange:
    start_offset_days: int
    end_offset_days: int


@dataclass(frozen=True)
class SparseLookbackMeta:
    detect_relation: str
    partition_date_expr: str
    updated_at_expr: str
    impact_range: SparseLookbackImpactRange | None = None


def _require_str(value: Any, *, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Expected non-empty string at {path}")
    return value.strip()


def _resolve_detect_relation(*, manifest: dict[str, Any], detect_source: dict[str, Any]) -> str:
    source_name = _require_str(detect_source.get("source"), path="meta.detect_source.source")
    table_name = _require_str(detect_source.get("table"), path="meta.detect_source.table")

    sources = manifest.get("sources") or {}
    matches: list[dict[str, Any]] = []
    for _unique_id, props in sources.items():
        if not isinstance(props, dict):
            continue
        if props.get("source_name") == source_name and props.get("name") == table_name:
            matches.append(props)

    if not matches:
        raise ValueError(f"dbt source not found in manifest: source('{source_name}','{table_name}')")
    if len(matches) > 1:
        unique_ids = sorted([str(m.get("unique_id")) for m in matches])
        raise ValueError(
            f"dbt source is ambiguous in manifest: source('{source_name}','{table_name}') (candidates: {unique_ids})"
        )

    props = matches[0]
    schema = props.get("schema")
    identifier = props.get("identifier") or props.get("name")
    if not schema or not identifier:
        raise ValueError(
            f"dbt source missing schema/identifier in manifest: source('{source_name}','{table_name}')"
        )
    return f"{schema}.{identifier}"


def parse_sparse_lookback_meta(
    *,
    meta: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> SparseLookbackMeta:
    detect_relation_value = meta.get("detect_relation")
    detect_source_value = meta.get("detect_source")

    if detect_relation_value is None and detect_source_value is None:
        raise ValueError("Sparse lookback meta requires either detect_relation or detect_source")

    if detect_relation_value is not None and detect_source_value is not None:
        raise ValueError("Sparse lookback meta cannot set both detect_relation and detect_source")

    if detect_relation_value is not None:
        detect_relation = _require_str(detect_relation_value, path="meta.detect_relation")
    else:
        if manifest is None:
            raise ValueError("Sparse lookback meta using detect_source requires manifest")
        if not isinstance(detect_source_value, dict):
            raise ValueError("meta.detect_source must be a dict")
        detect_relation = _resolve_detect_relation(manifest=manifest, detect_source=detect_source_value)

    partition_date_expr = _require_str(meta.get("partition_date_expr"), path="meta.partition_date_expr")
    updated_at_expr = _require_str(meta.get("updated_at_expr"), path="meta.updated_at_expr")

    if ";" in detect_relation or ";" in partition_date_expr or ";" in updated_at_expr:
        raise ValueError("Sparse lookback meta cannot contain ';'")

    impact = meta.get("impact")
    impact_range: SparseLookbackImpactRange | None = None
    if isinstance(impact, dict):
        impact_type = impact.get("type")
        if impact_type == "range":
            start_offset_days = int(impact.get("start_offset_days", 0))
            end_offset_days = int(impact.get("end_offset_days", 0))
            if start_offset_days > end_offset_days:
                raise ValueError("impact.start_offset_days cannot be greater than impact.end_offset_days")
            impact_range = SparseLookbackImpactRange(
                start_offset_days=start_offset_days,
                end_offset_days=end_offset_days,
            )
        else:
            raise ValueError(f"Unsupported impact type: {impact_type}")

    return SparseLookbackMeta(
        detect_relation=detect_relation,
        partition_date_expr=partition_date_expr,
        updated_at_expr=updated_at_expr,
        impact_range=impact_range,
    )


def _as_sql_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _as_sql_date(value: date) -> str:
    return value.strftime("%Y-%m-%d")


def _expand_impacted_dates(dates: set[date], impact_range: SparseLookbackImpactRange | None) -> set[date]:
    if not dates or impact_range is None:
        return dates

    expanded: set[date] = set()
    for d in dates:
        for offset in range(impact_range.start_offset_days, impact_range.end_offset_days + 1):
            expanded.add(d + timedelta(days=offset))
    return expanded


def detect_changed_partition_dates(
    *,
    starrocks,
    meta: SparseLookbackMeta,
    window_start: date,
    window_end: date,
    since_ts: datetime,
) -> set[date]:
    partition_date_expr = f"CAST(({meta.partition_date_expr}) AS DATE)"
    sql = "\n".join(
        [
            "SELECT DISTINCT",
            f"  {partition_date_expr} AS partition_date",
            f"FROM {meta.detect_relation}",
            "WHERE 1=1",
            f"  AND {partition_date_expr} >= '{_as_sql_date(window_start)}'",
            f"  AND {partition_date_expr} <= '{_as_sql_date(window_end)}'",
            f"  AND ({meta.updated_at_expr}) > '{_as_sql_datetime(since_ts)}'",
        ]
    )

    values = starrocks.query_first_column(sql)
    dates: set[date] = set()
    for v in values:
        if v is None:
            continue
        if isinstance(v, date) and not isinstance(v, datetime):
            dates.add(v)
            continue
        if isinstance(v, datetime):
            dates.add(v.date())
            continue
        dates.add(date.fromisoformat(str(v)))

    return _expand_impacted_dates(dates, meta.impact_range)

