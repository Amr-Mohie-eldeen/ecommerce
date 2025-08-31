from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from fastapi import APIRouter, HTTPException

from . import db
from .cache import cache_get, cache_set
from .repositories import (
    InMemoryOrderRepository,
    OrderRepository,
    SqlAlchemyOrderRepository,
)
from .schemas import Order, OrderCreate
from .events_adapter import emit_order_created
from .config import get_settings


router = APIRouter()


def get_repo() -> OrderRepository:
    if db.is_ready():
        return SqlAlchemyOrderRepository()
    return InMemoryOrderRepository()


@asynccontextmanager
async def _null_session():
    yield None


@router.post("/orders", status_code=201, response_model=Order)
async def create_order(body: OrderCreate) -> Order:
    repo = get_repo()
    sess_cm = db.session_scope() if db.is_ready() else _null_session()  # type: ignore
    async with sess_cm as session:  # type: ignore
        created = await repo.create(
            session,
            customer_id=body.customer_id,
            currency=body.currency,
            items=[i.model_dump() for i in body.items],
        )
    order_dict = {
        "id": created.id,
        "customer_id": created.customer_id,
        "status": created.status,
        "currency": created.currency,
        "total_amount": float(created.total_amount),
        "created_at": created.created_at,
        "items": [
            {
                "product_id": it.product_id,
                "quantity": it.quantity,
                "unit_price": float(it.unit_price),
            }
            for it in created.items
        ],
    }
    settings = get_settings()
    await cache_set(
        f"order:{created.id}",
        order_dict | {"created_at": None},
        ttl_seconds=settings.cache_ttl_seconds,
        cache_name="order",
    )
    asyncio.create_task(emit_order_created(order_dict))
    return Order(**order_dict)


@router.get("/orders/{id}", response_model=Order)
async def get_order(id: str) -> Order:
    cached = await cache_get(f"order:{id}", cache_name="order")
    if cached:
        return Order(**cached)
    repo = get_repo()
    sess_cm = db.session_scope() if db.is_ready() else _null_session()  # type: ignore
    async with sess_cm as session:  # type: ignore
        got = await repo.get(session, id)
    if not got:
        raise HTTPException(status_code=404, detail="Order not found")
    order_dict = {
        "id": got.id,
        "customer_id": got.customer_id,
        "status": got.status,
        "currency": got.currency,
        "total_amount": float(got.total_amount),
        "created_at": got.created_at,
        "items": [
            {
                "product_id": it.product_id,
                "quantity": it.quantity,
                "unit_price": float(it.unit_price),
            }
            for it in got.items
        ],
    }
    settings = get_settings()
    await cache_set(
        f"order:{id}",
        order_dict | {"created_at": None},
        ttl_seconds=settings.cache_ttl_seconds,
        cache_name="order",
    )
    return Order(**order_dict)
