# Dagster platform metrics

This document describes the OpenTelemetry metrics emitted by the Dagster platform `metrics-exporter` Deployment.

## Scope

These metrics represent **platform health** (orchestration control plane), not business-level pipeline metrics.

## Metric catalog

### Runs

- `dagster.run.queue.depth` (gauge, unit: `1`)
  - Meaning: number of runs in `QUEUED`.
  - Value: detects backlog and saturation.
  - Alert: warn if `> 0` for sustained period; critical if `> N` (cluster-specific).

- `dagster.run.queue.oldest_age_seconds` (gauge, unit: `s`)
  - Meaning: seconds since the oldest queued run was created.
  - Value: detects “queue stuck” even when depth is small.
  - Alert: warn if `> 300s`; critical if `> 900s`.

- `dagster.run.in_progress.count` (gauge, unit: `1`)
  - Meaning: number of runs in `NOT_STARTED`, `STARTING`, or `STARTED`.
  - Value: approximates platform activity and concurrency.
  - Alert: typically none by itself; use with queue metrics.

### Sensors and schedules

- `dagster.sensor.enabled.count` (gauge, unit: `1`)
  - Meaning: number of sensors in `RUNNING` status.
  - Value: quick “are sensors enabled?” check.
  - Alert: warn if unexpectedly `0`.

- `dagster.schedule.enabled.count` (gauge, unit: `1`)
  - Meaning: number of schedules in `RUNNING` status.
  - Value: quick “are schedules enabled?” check.
  - Alert: warn if unexpectedly `0`.

- `dagster.sensor.last_tick_age_seconds` (gauge, unit: `s`)
  - Attributes: `dagster.instigator_name`, `dagster.instigator_status`
  - Meaning: seconds since the latest sensor tick.
  - Value: detects stalled sensor evaluation.
  - Alert: warn if `> 300s`; critical if `> 900s` (tune to your sensor cadence).

- `dagster.schedule.last_tick_age_seconds` (gauge, unit: `s`)
  - Attributes: `dagster.instigator_name`, `dagster.instigator_status`
  - Meaning: seconds since the latest schedule tick.
  - Value: detects stalled scheduling loop.
  - Alert: warn if `> 600s`; critical if `> 1800s` (tune to your schedule cadence).

### Daemon health

- `dagster.daemon.heartbeat.count` (gauge, unit: `1`)
  - Meaning: number of heartbeat records visible to the instance.
  - Value: detects missing heartbeats globally.
  - Alert: critical if `== 0`.

- `dagster.daemon.heartbeat_age_seconds` (gauge, unit: `s`)
  - Attributes: `dagster.daemon_type`
  - Meaning: seconds since the most recent heartbeat for each daemon type.
  - Value: detects daemon stuck/crashloop/overload.
  - Alert: warn if `> 120s`; critical if `> 300s`.

- `dagster.daemon.heartbeat_errors.count` (gauge, unit: `1`)
  - Attributes: `dagster.daemon_type`
  - Meaning: number of errors recorded on recent heartbeats for each daemon type.
  - Value: surfaces internal daemon errors without scraping logs.
  - Alert: warn if `> 0` for sustained period.

## Notes

- Thresholds are starting points; tune them per environment and workload.
- Avoid adding labels that explode cardinality (for example run_id, partition key).
