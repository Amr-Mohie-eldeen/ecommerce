from __future__ import annotations

import asyncio
from fastapi import APIRouter, HTTPException
from contextlib import asynccontextmanager

from . import db
from .cache import cache_get, cache_set
from .repositories import (
    InMemoryProductRepository,
    ProductRepository,
    SqlAlchemyProductRepository,
)
from .schemas import Product, ProductCreate, SearchResult
from .search import search_products
from .events_adapter import emit_product_updated


router = APIRouter()


def get_repo() -> ProductRepository:
    # Use SQL repo when DB is ready; otherwise, memory repo
    if db.is_ready():
        return SqlAlchemyProductRepository()
    return InMemoryProductRepository()


@asynccontextmanager
async def _null_session():
    yield None


@router.post("/products", status_code=201, response_model=Product)
async def create_product(body: ProductCreate) -> Product:
    repo = get_repo()
    sess_cm = db.session_scope() if db.is_ready() else _null_session()  # type: ignore
    async with sess_cm as session:  # type: ignore
        created = await repo.create(
            session, name=body.name, price=body.price, description=body.description
        )
    product_dict = {
        "id": created.id,
        "name": created.name,
        "price": float(created.price),
        "description": created.description,
        "updated_at": created.updated_at,
    }
    # Cache by id
    await cache_set(
        f"product:{created.id}", product_dict | {"updated_at": None}, ttl_seconds=30
    )
    # Emit event asynchronously
    asyncio.create_task(emit_product_updated(product_dict))
    return Product(**product_dict)


@router.get("/products/{id}", response_model=Product)
async def get_product(id: str) -> Product:
    cached = await cache_get(f"product:{id}")
    if cached:
        return Product(**cached)

    repo = get_repo()
    sess_cm = db.session_scope() if db.is_ready() else _null_session()  # type: ignore
    async with sess_cm as session:  # type: ignore
        got = await repo.get(session, id)
    if not got:
        raise HTTPException(status_code=404, detail="Product not found")
    product_dict = {
        "id": got.id,
        "name": got.name,
        "price": float(got.price),
        "description": got.description,
        "updated_at": got.updated_at,
    }
    await cache_set(
        f"product:{id}", product_dict | {"updated_at": None}, ttl_seconds=30
    )
    return Product(**product_dict)


@router.get("/search", response_model=SearchResult)
async def search(q: str) -> SearchResult:
    # Simple cache for search queries
    key = f"search:{q}"
    cached = await cache_get(key)
    if cached and isinstance(cached.get("results"), list):
        return SearchResult(**cached)

    res = search_products(q)
    payload = {"query": q, "results": res}
    await cache_set(key, payload, ttl_seconds=15)
    return SearchResult(**payload)
