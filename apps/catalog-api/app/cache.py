from __future__ import annotations

import json
from typing import Any, Optional
from time import perf_counter

try:
    from prometheus_client import Counter, Histogram
except Exception:  # pragma: no cover
    Counter = None  # type: ignore
    Histogram = None  # type: ignore

try:
    from redis import asyncio as aioredis
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore

_redis = None
_hit_counter = (
    Counter("catalog_cache_hits_total", "Cache hits", ["cache"]) if Counter else None
)
_miss_counter = (
    Counter("catalog_cache_misses_total", "Cache misses", ["cache"])
    if Counter
    else None
)
_latency_hist = (
    Histogram("catalog_cache_latency_seconds", "Cache op latency", ["op", "cache"])
    if Histogram
    else None
)


def init_redis(redis_url: str | None):
    global _redis
    if not redis_url or aioredis is None:
        _redis = None
        return
    try:
        _redis = aioredis.from_url(redis_url, decode_responses=True)
    except Exception:
        _redis = None


async def cache_get(
    key: str, *, cache_name: str = "default"
) -> Optional[dict[str, Any]]:
    if _redis is None:
        return None
    try:
        start = perf_counter()
        val = await _redis.get(key)
        if _latency_hist:
            _latency_hist.labels("get", cache_name).observe(perf_counter() - start)
        if not val:
            if _miss_counter:
                _miss_counter.labels(cache_name).inc()
            return None
        if _hit_counter:
            _hit_counter.labels(cache_name).inc()
        return json.loads(val)
    except Exception:
        return None


async def cache_set(
    key: str, value: dict[str, Any], ttl_seconds: int, *, cache_name: str = "default"
) -> None:
    if _redis is None:
        return
    try:
        start = perf_counter()
        await _redis.setex(key, ttl_seconds, json.dumps(value))
        if _latency_hist:
            _latency_hist.labels("set", cache_name).observe(perf_counter() - start)
    except Exception:
        return


async def ping() -> bool:
    if _redis is None:
        return False
    try:
        await _redis.ping()
        return True
    except Exception:
        return False
