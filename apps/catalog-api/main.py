import os
from fastapi import FastAPI, BackgroundTasks, Response
from pydantic import BaseModel, Field
from typing import List
from events import publish_product_updated
from opensearchpy import OpenSearch


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0)
    description: str | None = None


class Product(BaseModel):
    id: str
    name: str
    price: float
    description: str | None = None


app = FastAPI(title="Catalog API", version="1.0.0")


def get_search_client():
    try:
        url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
        return OpenSearch(hosts=[url])
    except Exception:
        return None


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


@app.post("/products", status_code=201, response_model=Product)
def create_product(body: ProductCreate, background_tasks: BackgroundTasks):
    # Stubbed persistence; return a predictable id for tests
    created = Product(
        id="p-1", name=body.name, price=body.price, description=body.description
    )
    # Emit event in background (non-blocking)
    background_tasks.add_task(
        publish_product_updated,
        {"id": created.id, "name": created.name, "price": created.price},
    )
    return created


@app.get("/products/{id}", response_model=Product)
def get_product(id: str):
    # Stubbed read
    return Product(id=id, name="demo", price=9.99, description=None)


class SearchResult(BaseModel):
    query: str
    results: List[Product]


@app.get("/search", response_model=SearchResult)
def search(q: str):
    client = get_search_client()
    if not client or not q:
        return SearchResult(query=q, results=[])
    try:
        res = client.search(
            index="products",
            body={
                "size": 10,
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["name^2", "description"],
                    }
                },
            },
        )
        hits = res.get("hits", {}).get("hits", [])
        items = []
        for h in hits:
            src = h.get("_source", {})
            items.append(
                Product(
                    id=src.get("product_id", h.get("_id")),
                    name=src.get("name", ""),
                    price=float(src.get("price", 0.0)),
                    description=src.get("description"),
                )
            )
        return SearchResult(query=q, results=items)
    except Exception:
        return SearchResult(query=q, results=[])
