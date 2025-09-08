from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ProductORM


class ProductRepository:
    async def create(
        self, session: AsyncSession, *, name: str, price: float, description: str | None
    ) -> ProductORM:
        raise NotImplementedError

    async def get(self, session: AsyncSession, product_id: str) -> Optional[ProductORM]:
        raise NotImplementedError

    async def update(
        self,
        session: AsyncSession,
        product_id: str,
        *,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Optional[ProductORM]:
        raise NotImplementedError


class SqlAlchemyProductRepository(ProductRepository):
    async def create(
        self, session: AsyncSession, *, name: str, price: float, description: str | None
    ) -> ProductORM:
        pid = f"p-{uuid.uuid4().hex[:8]}"
        now = dt.datetime.now(dt.timezone.utc)
        stmt = insert(ProductORM).values(
            id=pid, name=name, price=price, description=description, updated_at=now
        )
        await session.execute(stmt)
        await session.commit()
        return await self.get(session, pid)  # type: ignore

    async def get(self, session: AsyncSession, product_id: str) -> Optional[ProductORM]:
        stmt = select(ProductORM).where(ProductORM.id == product_id).limit(1)
        res = await session.execute(stmt)
        row = res.scalar_one_or_none()
        return row

    async def update(
        self,
        session: AsyncSession,
        product_id: str,
        *,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Optional[ProductORM]:
        updates = {"updated_at": dt.datetime.now(dt.timezone.utc)}
        if name is not None:
            updates["name"] = name
        if price is not None:
            updates["price"] = price
        if description is not None:
            updates["description"] = description

        if len(updates) == 1:  # Only updated_at was set
            return await self.get(session, product_id)

        stmt = update(ProductORM).where(ProductORM.id == product_id).values(**updates)
        await session.execute(stmt)
        await session.commit()
        return await self.get(session, product_id)


_MEM_ITEMS: dict[str, ProductORM] = {}
_MEM_COUNTER = {"n": 0}


class InMemoryProductRepository(ProductRepository):
    def __init__(self):
        # Shared in-memory store across instances to persist within process
        self._items = _MEM_ITEMS

    async def create(
        self,
        session: AsyncSession,
        *,
        name: str,
        price: float,
        description: str | None,
    ) -> ProductORM:
        _MEM_COUNTER["n"] += 1
        pid = f"p-{_MEM_COUNTER['n']}"
        now = dt.datetime.now(dt.timezone.utc)
        item = ProductORM(id=pid, name=name, price=price, description=description, updated_at=now)  # type: ignore
        self._items[pid] = item
        return item

    async def get(self, session: AsyncSession, product_id: str) -> Optional[ProductORM]:
        return self._items.get(product_id)

    async def update(
        self,
        session: AsyncSession,
        product_id: str,
        *,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Optional[ProductORM]:
        item = self._items.get(product_id)
        if not item:
            return None
        if name is not None:
            item.name = name  # type: ignore
        if price is not None:
            item.price = price  # type: ignore
        if description is not None:
            item.description = description  # type: ignore
        item.updated_at = dt.datetime.now(dt.timezone.utc)  # type: ignore
        return item
