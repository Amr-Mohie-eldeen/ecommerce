from __future__ import annotations

import json
from typing import Any, Optional

try:
    from redis import asyncio as aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

_redis = None


def init_redis(redis_url: str | None):
    global _redis
    if not redis_url or aioredis is None:
        _redis = None
        return
    try:
        _redis = aioredis.from_url(redis_url, decode_responses=True)
    except Exception:
        _redis = None


async def cache_get(key: str) -> Optional[dict[str, Any]]:
    if _redis is None:
        return None
    try:
        val = await _redis.get(key)
        if not val:
            return None
        return json.loads(val)
    except Exception:
        return None


async def cache_set(key: str, value: dict[str, Any], ttl_seconds: int) -> None:
    if _redis is None:
        return
    try:
        await _redis.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        return
