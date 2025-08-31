from fastapi import FastAPI, Response

app = FastAPI(title="Recommender Service", version="1.0.0")


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


@app.get("/recommendations")
def recommendations(customer_id: str):
    return {"customer_id": customer_id, "recommendations": []}
