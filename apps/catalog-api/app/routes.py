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
from .schemas import Product, ProductCreate, ProductUpdate, SearchResult
from .search import search_products
from .events_adapter import emit_product_updated
from .config import get_settings


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
    settings = get_settings()
    await cache_set(
        f"product:{created.id}",
        product_dict | {"updated_at": None},
        ttl_seconds=settings.cache_ttl_seconds,
        cache_name="product",
    )
    # Emit event asynchronously
    asyncio.create_task(emit_product_updated(product_dict))
    return Product(**product_dict)


@router.get("/products/{id}", response_model=Product)
async def get_product(id: str) -> Product:
    cached = await cache_get(f"product:{id}", cache_name="product")
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
    settings = get_settings()
    await cache_set(
        f"product:{id}",
        product_dict | {"updated_at": None},
        ttl_seconds=settings.cache_ttl_seconds,
        cache_name="product",
    )
    return Product(**product_dict)


@router.get("/search", response_model=SearchResult)
async def search(q: str) -> SearchResult:
    # Simple cache for search queries
    key = f"search:{q}"
    cached = await cache_get(key, cache_name="search")
    if cached and isinstance(cached.get("results"), list):
        return SearchResult(**cached)

    res = search_products(q)
    payload = {"query": q, "results": res}
    settings = get_settings()
    await cache_set(
        key,
        payload,
        ttl_seconds=settings.search_cache_ttl_seconds,
        cache_name="search",
    )
    return SearchResult(**payload)


@router.put("/products/{id}", response_model=Product)
async def update_product(id: str, body: ProductUpdate) -> Product:
    repo = get_repo()
    sess_cm = db.session_scope() if db.is_ready() else _null_session()  # type: ignore
    async with sess_cm as session:  # type: ignore
        updated = await repo.update(
            session,
            id,
            name=body.name,
            price=body.price,
            description=body.description,
        )
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")

    product_dict = {
        "id": updated.id,
        "name": updated.name,
        "price": float(updated.price),
        "description": updated.description,
        "updated_at": updated.updated_at,
    }
    # Invalidate cache and set fresh value
    settings = get_settings()
    await cache_set(
        f"product:{id}",
        product_dict | {"updated_at": None},
        ttl_seconds=settings.cache_ttl_seconds,
        cache_name="product",
    )
    asyncio.create_task(emit_product_updated(product_dict))
    return Product(**product_dict)
