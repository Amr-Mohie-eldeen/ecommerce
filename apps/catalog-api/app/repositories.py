from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ProductORM


class ProductRepository:
    async def create(
        self, session: AsyncSession, *, name: str, price: float, description: str | None
    ) -> ProductORM:
        raise NotImplementedError

    async def get(self, session: AsyncSession, product_id: str) -> Optional[ProductORM]:
        raise NotImplementedError


class SqlAlchemyProductRepository(ProductRepository):
    async def create(
        self, session: AsyncSession, *, name: str, price: float, description: str | None
    ) -> ProductORM:
        pid = f"p-{uuid.uuid4().hex[:8]}"
        now = dt.datetime.utcnow()
        stmt = insert(ProductORM).values(
            id=pid, name=name, price=price, description=description, updated_at=now
        )
        await session.execute(stmt)
        # Return entity
        return ProductORM(id=pid, name=name, price=price, description=description, updated_at=now)  # type: ignore

    async def get(self, session: AsyncSession, product_id: str) -> Optional[ProductORM]:
        stmt = select(ProductORM).where(ProductORM.id == product_id).limit(1)
        res = await session.execute(stmt)
        row = res.scalar_one_or_none()
        return row


# Fallback in-memory repo for environments without DB (e.g., unit tests)
_MEM_STORE: dict[str, ProductORM] = {}


class InMemoryProductRepository(ProductRepository):
    def __init__(self):
        # shared store across instances
        self._items = _MEM_STORE

    async def create(
        self,
        session: AsyncSession | None,
        *,
        name: str,
        price: float,
        description: str | None,
    ) -> ProductORM:
        pid = "p-1" if "p-1" not in self._items else f"p-{len(self._items)+1}"
        now = dt.datetime.utcnow()
        item = ProductORM(id=pid, name=name, price=price, description=description, updated_at=now)  # type: ignore
        self._items[pid] = item
        return item

    async def get(
        self, session: AsyncSession | None, product_id: str
    ) -> Optional[ProductORM]:
        return self._items.get(product_id)
