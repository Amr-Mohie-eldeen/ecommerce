from fastapi import FastAPI

app = FastAPI(title="Orders API", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/orders", status_code=201)
def create_order():
    return {"status": "ok", "message": "Order created (stub)"}


@app.get("/orders/{id}")
def get_order(id: str):
    return {"id": id, "status": "CREATED", "total": 42.0}
