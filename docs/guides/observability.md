# Observability (OpenTelemetry + Elastic APM)

This guide documents how Luban CI integrates OpenTelemetry (OTel) into Dagster platform deployments and how to export telemetry to backends such as Elastic APM.

Luban CI keeps observability opt-in by default: developers can focus on functional development and testing, while platform/DevOps engineers enable and tune export per environment.

## Scope

This guide covers:

- OpenTelemetry environment variable propagation for Dagster platform, code locations, and run pods (Kubernetes Jobs).
- How to enable export via GitOps configuration.
- Dagster platform health metrics emitted by the `metrics-exporter` deployment.

This guide does not cover business-level pipeline metrics.

## Architecture

### Shared configuration: `dagster-observability` ConfigMap

The Dagster platform GitOps template provides a `dagster-observability` ConfigMap that is injected into:

- Dagster webserver/daemon pods, and
- Kubernetes Job pods launched by `K8sRunLauncher`

This standardizes propagation of OTEL environment variables (for example `OTEL_EXPORTER_OTLP_ENDPOINT`) without requiring changes in application repos.

The `dagster-observability` ConfigMap is platform-owned and shared within a namespace. Code locations consume it but should not define their own copy (to avoid cross-app collisions).

### Service identity

To support distinct service identity per workload, `OTEL_SERVICE_NAME` is set explicitly in each Deployment (platform components and code locations) and overrides any value that may be present in the shared ConfigMap.

### Default behavior (opt-in)

By default, the template sets:

- `OTEL_TRACES_EXPORTER=none`
- `OTEL_METRICS_EXPORTER=none`

To enable export, override these values (for example set `OTEL_TRACES_EXPORTER=otlp`) in your GitOps repo overlays.

If export is enabled but `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_PROTOCOL` are missing or invalid, the Dagster platform bootstrap logs a warning and disables export for that signal.

## Enabling export (GitOps)

OTEL configuration is centralized in the `luban-config` ConfigMap with empty defaults to disable export when not needed:

```yaml
data:
  otel_exporter_otlp_endpoint: ""  # Empty = disabled
  otel_exporter_otlp_protocol: ""  # Empty = disabled
```

When observability is needed, set these values in your environment's `luban-config` overlay:

```yaml
data:
  otel_exporter_otlp_endpoint: "http://elastic-apm-server.monitoring:8200"
  otel_exporter_otlp_protocol: "http/protobuf"  # or "grpc"
```

If your OTLP endpoint requires authentication (for example Elastic APM secret token), set `OTEL_EXPORTER_OTLP_HEADERS` via your GitOps overlay/secret mechanism. The value is a comma-separated list of `key=value` pairs (for example `Authorization=Bearer <token>`).

## Elastic APM example

Example values for an in-cluster Elastic APM Server (OTLP/HTTP):

```yaml
data:
  OTEL_TRACES_EXPORTER: "otlp"
  OTEL_METRICS_EXPORTER: "otlp"
  OTEL_EXPORTER_OTLP_PROTOCOL: "http/protobuf"
  OTEL_EXPORTER_OTLP_ENDPOINT: "http://<apm-service>.<apm-namespace>:8200"
  OTEL_RESOURCE_ATTRIBUTES: "deployment.environment=snd,project.name=<project>"
```

To find the APM service name and port:

```bash
kubectl -n <apm-namespace> get svc | grep -i apm
kubectl -n <apm-namespace> describe svc <apm-service>
```

Recommended resource attributes:

- `deployment.environment` (e.g. snd, prd)
- `project.name` (your project identifier)
- For platform pods: `dagster.component` (webserver, daemon, metrics-exporter)
- For code-location pods: `dagster.code_location` (app name)
- `service.name` is already set via `OTEL_SERVICE_NAME`; add `service.version` only if you accept the metric-cardinality impact

## Dagster platform metrics

This section describes the OpenTelemetry metrics emitted by the Dagster platform `metrics-exporter` Deployment.

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

### Notes

- Thresholds are starting points; tune them per environment and workload.
- Avoid adding labels that explode cardinality (for example run_id, partition key).

