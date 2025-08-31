from fastapi.testclient import TestClient
import os
import sys

# Add app module path so we can import 'main' despite hyphenated folder name
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import app


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_create_and_get_product():
    payload = {"name": "Widget", "price": 9.99}
    r = client.post("/products", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "p-1"
    assert data["name"] == payload["name"]

    r2 = client.get(f"/products/{data['id']}")
    assert r2.status_code == 200
    got = r2.json()
    assert got["id"] == data["id"]


def test_search_empty_results():
    r = client.get("/search", params={"q": "foo"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "foo"
    assert body["results"] == []
