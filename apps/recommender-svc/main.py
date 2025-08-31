import os
from fastapi import FastAPI

PORT = int(os.getenv("PORT", 8003))

app = FastAPI(title="Recommender Service", version="1.0.0")


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/recommendations")
def recommendations(customer_id: str):
    return {"customer_id": customer_id, "recommendations": []}
