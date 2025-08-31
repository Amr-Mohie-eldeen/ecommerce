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

    async def update(
        self,
        session: AsyncSession,
        product_id: str,
        *,
        name: Optional[str] = None,
        price: Optional[float] = None,
        description: Optional[str] = None,
    ) -> Optional[ProductORM]:
        sets = {}
        if name is not None:
            sets[ProductORM.name] = name
        if price is not None:
            sets[ProductORM.price] = price
        if description is not None:
            sets[ProductORM.description] = description
        if not sets:
            return await self.get(session, product_id)
        sets[ProductORM.updated_at] = dt.datetime.utcnow()
        stmt = (
            update(ProductORM)
            .where(ProductORM.id == product_id)
            .values(**{c.key: v for c, v in sets.items()})
            .returning(
                ProductORM.id,
                ProductORM.name,
                ProductORM.price,
                ProductORM.description,
                ProductORM.updated_at,
            )
        )
        res = await session.execute(stmt)
        row = res.first()
        if not row:
            return None
        return ProductORM(
            id=row[0], name=row[1], price=row[2], description=row[3], updated_at=row[4]  # type: ignore
        )


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

    async def update(
        self,
        session: AsyncSession | None,
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
        item.updated_at = dt.datetime.utcnow()  # type: ignore
        return item
