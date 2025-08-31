from __future__ import annotations

from fastapi import FastAPI, Response

from .config import get_settings
from . import db
from .models import Base
from .cache import init_redis
from .routes import router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Catalog API", version="1.0.0")

    # DB init (best-effort). If fails, app continues with in-memory repo.
    if settings.db_url:
        try:
            db.init_engine(settings.db_url)
        except Exception:
            pass

    # Redis cache init (best-effort)
    init_redis(settings.redis_url)

    # Health
    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    # Prometheus metrics endpoint
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

    # Include routes
    app.include_router(router)

    # On startup, attempt to create tables
    @app.on_event("startup")
    async def on_startup():
        try:
            await db.create_all(Base.metadata)
        except Exception:
            pass

    return app
