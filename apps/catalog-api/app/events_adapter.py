from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from events import publish_product_updated_async
from .config import get_settings
import os

try:
    from fastavro import parse_schema, validate
except Exception:  # pragma: no cover
    parse_schema = None  # type: ignore
    validate = None  # type: ignore
_parsed_schema = None


async def emit_product_updated(product: Dict[str, Any]) -> None:
    payload = {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "description": product.get("description"),
        "updated_at": int(datetime.now(timezone.utc).timestamp() * 1000),
    }
    settings = get_settings()
    if settings.validate_avro and parse_schema and validate:
        try:
            global _parsed_schema
            if _parsed_schema is None:
                schema_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "..",
                    "contracts",
                    "avro",
                    "ProductUpdated.avsc",
                )
                schema_path = os.path.abspath(schema_path)
                import json

                with open(schema_path) as f:
                    _parsed_schema = parse_schema(json.load(f))
            validate(
                {
                    "event_id": payload["id"],
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "product_id": payload["id"],
                    "name": payload.get("name") or "",
                    "description": payload.get("description") or "",
                    "price": float(payload.get("price") or 0),
                    "stock_qty": 0,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                _parsed_schema,
            )
        except Exception:
            # best-effort: don't block publishing
            pass
    await publish_product_updated_async(payload)
