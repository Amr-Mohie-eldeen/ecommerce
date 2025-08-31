import os
from fastapi import FastAPI

PORT = int(os.getenv("PORT", 8001))

app = FastAPI(title="Catalog API", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/products", status_code=201)
def create_product():
    return {"status": "ok", "message": "Product created (stub)"}


@app.get("/products/{id}")
def get_product(id: str):
    return {"id": id, "name": "demo", "price": 9.99}


@app.get("/search")
def search(q: str):
    return {"query": q, "results": []}
