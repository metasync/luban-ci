import os
import sys
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter as GrpcOTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as GrpcOTLPSpanExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as HttpOTLPMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter as HttpOTLPSpanExporter,
)
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def _otel_protocol() -> str:
    return (os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL") or "http/protobuf").strip().lower()


def _otlp_endpoint() -> Optional[str]:
    value = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if value is None:
        return None
    value = value.strip()
    return value or None


def _service_name() -> Optional[str]:
    value = os.getenv("OTEL_SERVICE_NAME")
    if value is None:
        return None
    value = value.strip()
    return value or None


def _enabled(value: Optional[str]) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized not in {"", "none", "false", "0"}


def _resource_attributes() -> dict[str, str]:
    raw = os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    if raw is None:
        return {}

    raw = raw.strip()
    if not raw:
        return {}

    attributes: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        attributes[key] = value
    return attributes


def _resource() -> Resource:
    attributes = _resource_attributes()
    service_name = _service_name()
    if service_name:
        attributes[SERVICE_NAME] = service_name
    return Resource.create(attributes)


def _warn(message: str) -> None:
    print(message, file=sys.stderr)


def _validate_export_enabled(signal: str) -> bool:
    exporter_key = f"OTEL_{signal}_EXPORTER"
    exporter_value = os.getenv(exporter_key)
    if not _enabled(exporter_value):
        return False

    endpoint = _otlp_endpoint()
    if endpoint is None:
        _warn(
            f"{exporter_key} is enabled but OTEL_EXPORTER_OTLP_ENDPOINT is empty; disabling {signal.lower()} export"
        )
        return False

    protocol = _otel_protocol()
    if protocol not in {"grpc", "http/protobuf"}:
        _warn(
            f"OTEL_EXPORTER_OTLP_PROTOCOL={protocol!r} is invalid; disabling {signal.lower()} export"
        )
        return False

    if protocol != "grpc" and not (endpoint.startswith("http://") or endpoint.startswith("https://")):
        _warn(
            f"OTEL_EXPORTER_OTLP_ENDPOINT={endpoint!r} must be an http(s) URL for protocol {protocol!r}; disabling {signal.lower()} export"
        )
        return False

    return True


def configure_tracing() -> None:
    if not _validate_export_enabled("TRACES"):
        return

    protocol = _otel_protocol()
    exporter = GrpcOTLPSpanExporter() if protocol == "grpc" else HttpOTLPSpanExporter()

    resource = _resource()

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def configure_metrics(export_interval_millis: int = 60000) -> None:
    if not _validate_export_enabled("METRICS"):
        return

    protocol = _otel_protocol()
    exporter = GrpcOTLPMetricExporter() if protocol == "grpc" else HttpOTLPMetricExporter()
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval_millis)

    resource = _resource()

    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)


def configure_otel(export_interval_millis: int = 60000) -> None:
    configure_tracing()
    configure_metrics(export_interval_millis=export_interval_millis)
