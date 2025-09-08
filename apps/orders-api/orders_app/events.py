import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional
from datetime import datetime, timezone

try:
    from aiokafka import AIOKafkaProducer
except Exception:  # pragma: no cover
    AIOKafkaProducer = None  # type: ignore


_producer: Optional["AIOKafkaProducer"] = None
_producer_lock = asyncio.Lock()


def kafka_enabled() -> bool:
    if os.getenv("DISABLE_KAFKA", "").lower() in {"1", "true", "yes", "on"}:
        return False
    if os.getenv("PYTEST_CURRENT_TEST"):
        return False
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
                    f"[orders-events] Kafka producer init failed: {e}. Falling back to stdout.",
                    file=sys.stderr,
                )
                _producer = None
    return _producer


async def publish_order_created_async(event: Dict[str, Any]) -> None:
    topic = os.getenv("TOPIC_ORDER_CREATED", "events.orders.order-created")
    if "created_at" not in event:
        event["created_at"] = datetime.now(timezone.utc).isoformat()
    prod = await _ensure_producer()
    if prod is None:
        print(
            f"[orders-events] OrderCreated (stdout): {json.dumps(event)}",
            file=sys.stdout,
        )
        return
    try:
        key = str(event.get("order_id", "")).encode() if event.get("order_id") else None
        await prod.send_and_wait(topic, json.dumps(event).encode("utf-8"), key=key)
    except Exception as e:
        print(
            f"[orders-events] Kafka publish failed: {e}. Event: {event}",
            file=sys.stderr,
        )


def publish_order_created(event: Dict[str, Any]) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(publish_order_created_async(event))
    except RuntimeError:
        print(
            f"[orders-events] OrderCreated (stdout): {json.dumps(event)}",
            file=sys.stdout,
        )
