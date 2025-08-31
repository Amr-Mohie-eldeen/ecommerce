from __future__ import annotations

import datetime as dt
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., ge=0)
    description: str | None = None


class Product(BaseModel):
    id: str
    name: str
    price: float
    description: str | None = None
    updated_at: dt.datetime | None = None


class SearchResult(BaseModel):
    query: str
    results: list[Product]
