import json
import logging
import time

from fastapi import Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger("pulso.http")


class Metrics:
    def __init__(self):
        self.registry = CollectorRegistry()
        self.requests = Counter(
            "pulso_http_requests_total",
            "Product API requests",
            ["method", "route", "status"],
            registry=self.registry,
        )
        self.latency = Histogram(
            "pulso_http_duration_seconds",
            "Product API latency",
            ["route"],
            registry=self.registry,
            buckets=(0.025, 0.05, 0.1, 0.2, 0.4, 0.7, 1, 3, 10),
        )
        self.eligible = Histogram(
            "pulso_eligible_videos",
            "Observed eligible coverage",
            ["country", "period"],
            registry=self.registry,
            buckets=(0, 5, 10, 17, 20, 30, 50, 100),
        )
        self.jobs = Counter("pulso_jobs_total", "Job outcomes", ["kind", "state"], registry=self.registry)
        self.stage_duration = Histogram(
            "pulso_job_duration_seconds", "Job duration", ["kind"], registry=self.registry
        )
        self.pending = Gauge("pulso_outbox_pending", "Pending scheduling envelopes", registry=self.registry)


def install(app, settings):
    app.state.metrics = Metrics()

    @app.middleware("http")
    async def observe(request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        if path not in {"/metrics", "/health", "/ready"}:
            elapsed = time.perf_counter() - started
            app.state.metrics.requests.labels(request.method, path, str(response.status_code)).inc()
            app.state.metrics.latency.labels(path).observe(elapsed)
            logger.info(
                json.dumps(
                    {
                        "method": request.method,
                        "route": path,
                        "status": response.status_code,
                        "duration_ms": round(elapsed * 1000, 2),
                    }
                )
            )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(app.state.metrics.registry), media_type=CONTENT_TYPE_LATEST)

    if settings.telemetry_enabled:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        provider = TracerProvider(resource=Resource.create({"service.name": "pulso-api"}))
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(provider)
        FastAPIInstrumentor.instrument_app(
            app, excluded_urls="health,metrics,ready", tracer_provider=provider
        )
