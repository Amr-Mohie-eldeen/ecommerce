from __future__ import annotations

import datetime as dt
from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: float = Field(..., ge=0)


class OrderCreate(BaseModel):
    customer_id: str = Field(..., min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    items: list[OrderItemCreate]


class OrderItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class Order(BaseModel):
    id: str
    customer_id: str
    status: str
    currency: str
    total_amount: float
    created_at: dt.datetime | None = None
    items: list[OrderItem]
