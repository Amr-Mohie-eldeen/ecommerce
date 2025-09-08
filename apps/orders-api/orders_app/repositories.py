from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import OrderItemORM, OrderORM


class OrderRepository:
    async def create(
        self,
        session: AsyncSession,
        *,
        customer_id: str,
        currency: str,
        items: list[dict],
    ) -> OrderORM:
        raise NotImplementedError

    async def get(self, session: AsyncSession, order_id: str) -> Optional[OrderORM]:
        raise NotImplementedError


class SqlAlchemyOrderRepository(OrderRepository):
    async def create(
        self,
        session: AsyncSession,
        *,
        customer_id: str,
        currency: str,
        items: list[dict],
    ) -> OrderORM:
        oid = f"o-{uuid.uuid4().hex[:8]}"
        now = dt.datetime.now(dt.timezone.utc)
        total = sum(float(i["unit_price"]) * int(i["quantity"]) for i in items)
        await session.execute(
            insert(OrderORM).values(
                id=oid,
                customer_id=customer_id,
                currency=currency,
                total_amount=total,
                status="CREATED",
                created_at=now,
            )
        )
        for i in items:
            await session.execute(
                insert(OrderItemORM).values(
                    order_id=oid,
                    product_id=i["product_id"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                )
            )
        return OrderORM(
            id=oid,
            customer_id=customer_id,
            currency=currency,
            total_amount=total,
            status="CREATED",
            created_at=now,
            items=[
                OrderItemORM(
                    order_id=oid,
                    product_id=i["product_id"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                )
                for i in items
            ],
        )  # type: ignore

    async def get(self, session: AsyncSession, order_id: str) -> Optional[OrderORM]:
        res = await session.execute(
            select(OrderORM).where(OrderORM.id == order_id).limit(1)
        )
        order = res.scalar_one_or_none()
        if not order:
            return None
        items_res = await session.execute(
            select(OrderItemORM).where(OrderItemORM.order_id == order_id)
        )
        order.items = list(items_res.scalars().all())  # type: ignore
        return order


_MEM_ORDERS: dict[str, OrderORM] = {}
_MEM_ITEMS: dict[str, list[OrderItemORM]] = {}


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders = _MEM_ORDERS
        self._items = _MEM_ITEMS

    async def create(
        self,
        session: AsyncSession | None,
        *,
        customer_id: str,
        currency: str,
        items: list[dict],
    ) -> OrderORM:
        oid = "o-1" if "o-1" not in self._orders else f"o-{len(self._orders)+1}"
        now = dt.datetime.now(dt.timezone.utc)
        total = sum(float(i["unit_price"]) * int(i["quantity"]) for i in items)
        order = OrderORM(id=oid, customer_id=customer_id, currency=currency, total_amount=total, status="CREATED", created_at=now)  # type: ignore
        self._orders[oid] = order
        self._items[oid] = [
            OrderItemORM(order_id=oid, product_id=i["product_id"], quantity=i["quantity"], unit_price=i["unit_price"])  # type: ignore
            for i in items
        ]
        order.items = self._items[oid]  # type: ignore
        return order

    async def get(
        self, session: AsyncSession | None, order_id: str
    ) -> Optional[OrderORM]:
        order = self._orders.get(order_id)
        if not order:
            return None
        order.items = self._items.get(order_id, [])  # type: ignore
        return order
