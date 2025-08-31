import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

try:
    from aiokafka import AIOKafkaProducer
except Exception:  # pragma: no cover
    AIOKafkaProducer = None  # type: ignore


_producer: Optional["AIOKafkaProducer"] = None
_producer_lock = asyncio.Lock()


def kafka_enabled() -> bool:
    return os.getenv("ENABLE_KAFKA", "false").lower() in {"1", "true", "yes", "on"}


async def _ensure_producer() -> Optional["AIOKafkaProducer"]:
    global _producer
    if _producer is not None:
        return _producer
    if not kafka_enabled() or AIOKafkaProducer is None:
        return None
    async with _producer_lock:
        if _producer is None:
            bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
            try:
                prod = AIOKafkaProducer(bootstrap_servers=bootstrap)
                await prod.start()
                _producer = prod
            except Exception as e:  # graceful fallback
                print(
                    f"[events] Kafka producer init failed: {e}. Falling back to stdout.",
                    file=sys.stderr,
                )
                _producer = None
    return _producer


async def publish_product_updated_async(event: Dict[str, Any]) -> None:
    topic = os.getenv("TOPIC_PRODUCT_UPDATED", "events.catalog.product-updated")
    prod = await _ensure_producer()
    if prod is None:
        print(f"[events] ProductUpdated (stdout): {json.dumps(event)}", file=sys.stdout)
        return
    try:
        key = str(event.get("id", "")).encode() if event.get("id") else None
        await prod.send_and_wait(topic, json.dumps(event).encode("utf-8"), key=key)
    except Exception as e:
        print(f"[events] Kafka publish failed: {e}. Event: {event}", file=sys.stderr)


def publish_product_updated(event: Dict[str, Any]) -> None:
    # Back-compat sync API; schedule async publish if loop exists
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(publish_product_updated_async(event))
    except RuntimeError:
        # No running loop; fallback to stdout
        print(f"[events] ProductUpdated (stdout): {json.dumps(event)}", file=sys.stdout)
