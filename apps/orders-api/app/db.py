from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

_engine = None
_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def init_engine(db_url: str) -> None:
    global _engine, _session_maker
    _engine = create_async_engine(db_url, future=True, echo=False)
    _session_maker = async_sessionmaker(_engine, expire_on_commit=False)


def is_ready() -> bool:
    return _session_maker is not None


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    if _session_maker is None:
        raise RuntimeError("DB not initialized")
    async with _session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def healthcheck() -> bool:
    if _engine is None:
        return False
    try:
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def create_all(metadata) -> None:
    if _engine is None:
        return
    async with _engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
