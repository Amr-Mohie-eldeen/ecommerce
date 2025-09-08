from __future__ import annotations

from fastapi import FastAPI, Response, HTTPException
from contextlib import asynccontextmanager

from .config import get_settings
from . import db
from .models import Base
from .cache import init_redis, ping as redis_ping
from .routes import router
from .errors import http_exception_handler

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            await db.create_all(Base.metadata)
        except Exception:
            pass
        if settings.otlp_endpoint:
            try:
                resource = Resource.create({"service.name": settings.service_name})
                provider = TracerProvider(resource=resource)
                trace.set_tracer_provider(provider)
                exporter = OTLPSpanExporter(
                    endpoint=settings.otlp_endpoint, insecure=True
                )
                provider.add_span_processor(BatchSpanProcessor(exporter))
                FastAPIInstrumentor.instrument_app(app)
                SQLAlchemyInstrumentor().instrument(
                    enable_commenter=True,
                    commenter_options={"db_framework": "sqlalchemy"},
                )
            except Exception:
                pass
        yield

    app = FastAPI(title="Orders API", version="1.0.0", lifespan=lifespan)
    app.add_exception_handler(HTTPException, http_exception_handler)

    if settings.db_url:
        try:
            db.init_engine(settings.db_url)
        except Exception:
            pass
    init_redis(settings.redis_url)

    @app.get("/healthz")
    async def healthz():
        return {"status": "ok"}

    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    except Exception:  # pragma: no cover
        CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

        def generate_latest():  # type: ignore
            return b""

    @app.get("/metrics")
    def metrics() -> Response:
        payload = generate_latest()
        return Response(content=payload, media_type=CONTENT_TYPE_LATEST)

    @app.get("/readyz")
    async def readyz():
        db_ok = await db.healthcheck() if settings.db_url else True
        redis_ok = await redis_ping()
        ok = db_ok  # redis optional
        return {
            "status": "ok" if ok else "degraded",
            "checks": {"db": db_ok, "redis": redis_ok},
        }

    app.include_router(router)

    return app
