from fastapi import FastAPI
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)


class Order(BaseModel):
    id: str
    status: str
    total: float


app = FastAPI(title="Orders API", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/orders", status_code=201, response_model=Order)
def create_order(body: OrderCreate):
    # Stub calculation for total; assume price 42 per unit
    return Order(id="o-1", status="CREATED", total=42.0 * body.quantity)


@app.get("/orders/{id}", response_model=Order)
def get_order(id: str):
    return Order(id=id, status="CREATED", total=42.0)
