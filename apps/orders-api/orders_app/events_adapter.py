from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Any, Dict

from .config import get_settings
from .events import publish_order_created_async

try:
    from fastavro import parse_schema, validate
except Exception:  # pragma: no cover
    parse_schema = None  # type: ignore
    validate = None  # type: ignore

_parsed_schema = None


async def emit_order_created(order: Dict[str, Any]) -> None:
    payload = {
        "event_id": order["id"],
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "order_id": order["id"],
        "customer_id": order["customer_id"],
        "items": order["items"],
        "total_amount": float(order["total_amount"]),
        "currency": order.get("currency", "USD"),
        "status": order.get("status", "CREATED"),
        "created_at": (
            order.get("created_at") or datetime.now(timezone.utc)
        ).isoformat(),
    }

    settings = get_settings()
    if settings.validate_avro and parse_schema and validate:
        try:
            global _parsed_schema
            if _parsed_schema is None:
                schema_path = os.path.abspath(
                    os.path.join(
                        os.path.dirname(os.path.dirname(__file__)),
                        "..",
                        "contracts",
                        "avro",
                        "OrderCreated.avsc",
                    )
                )
                import json

                with open(schema_path) as f:
                    _parsed_schema = parse_schema(json.load(f))
            validate(payload, _parsed_schema)
        except Exception:
            pass

    await publish_order_created_async(payload)
