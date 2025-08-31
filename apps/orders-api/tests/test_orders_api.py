from fastapi.testclient import TestClient
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_order():
    payload = {"product_id": "p-1", "quantity": 2}
    r = client.post("/orders", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "o-1"
    assert data["status"] == "CREATED"
    assert data["total"] == 84.0

    r2 = client.get(f"/orders/{data['id']}")
    assert r2.status_code == 200
    got = r2.json()
    assert got["id"] == data["id"]
    assert got["status"] == "CREATED"
