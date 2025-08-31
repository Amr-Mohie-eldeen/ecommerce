from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List
from events import publish_product_updated


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


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


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
    return SearchResult(query=q, results=[])
