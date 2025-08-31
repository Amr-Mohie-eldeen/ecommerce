from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from events import publish_product_updated_async


async def emit_product_updated(product: Dict[str, Any]) -> None:
    payload = {
        "id": product["id"],
        "name": product["name"],
        "price": product["price"],
        "description": product.get("description"),
        "updated_at": int(dt.datetime.utcnow().timestamp() * 1000),
    }
    await publish_product_updated_async(payload)
