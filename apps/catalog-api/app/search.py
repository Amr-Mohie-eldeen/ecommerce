from __future__ import annotations

import os
from typing import Any, List

try:
    from opensearchpy import OpenSearch
except Exception:  # pragma: no cover
    OpenSearch = None  # type: ignore


def get_search_client():
    try:
        url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
        if OpenSearch is None:
            return None
        return OpenSearch(hosts=[url])
    except Exception:
        return None


def search_products(q: str) -> list[dict[str, Any]]:
    client = get_search_client()
    if not client or not q:
        return []
    try:
        res = client.search(
            index="products",
            body={
                "size": 10,
                "query": {
                    "multi_match": {
                        "query": q,
                        "fields": ["name^2", "description"],
                    }
                },
            },
        )
        hits = res.get("hits", {}).get("hits", [])
        items: List[dict[str, Any]] = []
        for h in hits:
            src = h.get("_source", {})
            items.append(
                {
                    "id": src.get("product_id", h.get("_id")),
                    "name": src.get("name", ""),
                    "price": float(src.get("price", 0.0)),
                    "description": src.get("description"),
                }
            )
        return items
    except Exception:
        return []


def ping() -> bool:
    client = get_search_client()
    try:
        if not client:
            return False
        return bool(client.ping())
    except Exception:
        return False
