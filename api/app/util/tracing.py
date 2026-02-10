#!/usr/bin/env python3
"""
OpenTelemetry tracing setup for the FastAPI application.
"""
import os
import logging
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

logger = logging.getLogger(__name__)

_HTTPX_INSTRUMENTED = False


def _bool_env(name: str) -> bool:
    value = os.getenv(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _build_exporter():
    protocol = os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf").strip().lower()
    if protocol == "grpc":
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        return OTLPSpanExporter()
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    return OTLPSpanExporter()


def setup_tracing(app: FastAPI) -> bool:
    """
    Configure OpenTelemetry tracing when enabled via environment variables.

    Returns:
        True if tracing is enabled and configured, otherwise False.
    """
    if getattr(app.state, "tracing_configured", False):
        return bool(getattr(app.state, "tracing_enabled", False))

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    enabled = _bool_env("OTEL_TRACING_ENABLED") or bool(endpoint)
    app.state.tracing_configured = True
    app.state.tracing_enabled = False

    if not enabled:
        logger.info("OpenTelemetry tracing disabled (set OTEL_TRACING_ENABLED=true to enable).")
        return False

    service_name = os.getenv("OTEL_SERVICE_NAME", "googlecalendartoluma-api")
    deployment_env = os.getenv("DEPLOYMENT_PROFILE", "dev")
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": app.version,
            "deployment.environment": deployment_env
        }
    )

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

    if not getattr(app.state, "otel_span_processor_configured", False):
        exporter = _build_exporter()
        span_processor = BatchSpanProcessor(exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        app.state.otel_span_processor_configured = True

    excluded_urls = os.getenv("OTEL_EXCLUDED_URLS", "/health|/health/").strip()
    FastAPIInstrumentor.instrument_app(app, excluded_urls=excluded_urls)

    global _HTTPX_INSTRUMENTED
    if not _HTTPX_INSTRUMENTED:
        HTTPXClientInstrumentor().instrument()
        _HTTPX_INSTRUMENTED = True

    app.state.tracing_enabled = True
    logger.info("OpenTelemetry tracing enabled for service: %s", service_name)
    if endpoint:
        logger.info("OpenTelemetry OTLP endpoint: %s", endpoint)
    return True
